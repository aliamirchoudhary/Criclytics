"""App-owned JSON snapshots. Published generations are never mutated in place."""
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
import json
import threading
from .json_io import read_json


class JsonRepository:
    def __init__(self, maximum=32):
        self.maximum = maximum
        self._entries = OrderedDict()
        self._lock = threading.RLock()
        self.parses = 0

    def _snapshot(self, path):
        path = Path(path).resolve()
        with self._lock:
            previous = self._entries.get(path)
            try:
                stat = path.stat()
                version = (stat.st_mtime_ns, stat.st_size)
                if previous and previous[0] == version:
                    self._entries.move_to_end(path)
                    return previous
                data = read_json(path)
                if not isinstance(data, (dict, list)):
                    raise ValueError('Invalid JSON root')
                # Build indexes before publishing a new generation under the lock.
                index = {}
                if path.name == 'completed_matches.json' and isinstance(data, dict):
                    for match in data.get('data', []):
                        mid = str(match.get('id') or match.get('unique_id') or '')
                        if mid:
                            index[mid] = match
                entry = (version, data, index)
                self._entries[path] = entry
                self.parses += 1
                while len(self._entries) > self.maximum:
                    self._entries.popitem(last=False)
                return entry
            except (OSError, ValueError, TypeError, AttributeError):
                # Failed replacements do not destroy a previously published generation.
                return previous

    def read(self, path):
        snapshot = self._snapshot(path)
        return deepcopy(snapshot[1]) if snapshot else None

    def match(self, path, match_id):
        snapshot = self._snapshot(path)
        return deepcopy(snapshot[2].get(str(match_id))) if snapshot else None

    def summaries(self, path):
        from .match_listing import summary
        snapshot = self._snapshot(path)
        if not snapshot:
            return []
        # No mutable snapshot references escape: projection owns its nested arrays.
        return [summary(m, completed=True) for m in snapshot[2].values()]


def safe_file(root, filename):
    root = Path(root).resolve()
    path = (root / filename).resolve()
    if not path.is_relative_to(root) or path.suffix != '.json':
        raise ValueError('Invalid artifact path')
    return path
