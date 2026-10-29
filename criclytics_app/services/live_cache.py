"""Atomic disk last-good cache, timestamped Redis acceleration and SQLite leases."""
import json
from pathlib import Path
import sqlite3
import time
import uuid
from contextlib import contextmanager

from .repository import safe_file
from .json_io import atomic_json, read_json


class LiveCache:
    def __init__(self, directory, redis=None, clock=time.time, maximum=128, diagnostics=None):
        self.diagnostics = diagnostics
        self.directory = Path(directory)
        self.redis = redis
        self.clock = clock
        self.maximum = maximum

    def event(self, name):
        if self.diagnostics: self.diagnostics.event(name)

    def entry(self, filename):
        path = safe_file(self.directory, filename)
        candidates = []
        try:
            raw = read_json(path)
            candidates.append(raw if isinstance(raw, dict) and raw.get('_cache_version') == 1
                              else {'written_at': path.stat().st_mtime, 'data': raw})
        except ValueError:
            self.event("cache_parse_failure")
        except OSError:
            pass
        if self.redis:
            try:
                raw = json.loads(self.redis.get('criclytics:v1:' + filename) or 'null')
                # TTL alone cannot establish the original fetch time.
                if isinstance(raw, dict) and raw.get('_cache_version') == 1:
                    candidates.append(raw)
            except Exception:
                pass
        candidates = [c for c in candidates if isinstance(c.get('written_at'), (int, float))
                      and c['written_at'] <= self.clock() and c.get('data') is not None]
        self.event('cache_hit' if candidates else 'cache_miss')
        return max(candidates, key=lambda c: c['written_at']) if candidates else None

    def read(self, filename):
        item = self.entry(filename)
        return item['data'] if item else None

    def age(self, filename):
        item = self.entry(filename)
        return max(0, self.clock() - item['written_at']) / 60 if item else float('inf')

    def write(self, filename, data, ttl_minutes=60):
        path = safe_file(self.directory, filename)
        if not path.exists() and sum(1 for _ in self.directory.glob('*.json')) >= self.maximum:
            self.event("cache_store_failure")
            return False
        envelope = {'_cache_version': 1, 'written_at': self.clock(), 'data': data}
        # Disk is authoritative durable stale fallback even when Redis expires.
        atomic_json(path, envelope)
        if self.redis:
            try:
                self.redis.set('criclytics:v1:' + filename, json.dumps(envelope),
                               ex=max(1, int(ttl_minutes * 60)))
            except Exception:
                pass
        return True

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.directory / 'refresh.sqlite3', timeout=2)
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS lease (provider TEXT PRIMARY KEY, owner TEXT, until REAL)')
            with conn:
                yield conn
        finally:
            conn.close()

    def acquire(self):
        # One provider-wide row, shared by workers using this disk volume. Arbitrary
        # IDs cannot allocate locks or lease rows. A crash expires after 30 seconds.
        owner = uuid.uuid4().hex
        with self.connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            row = conn.execute("SELECT until FROM lease WHERE provider='cricapi'").fetchone()
            if row and row[0] > self.clock():
                return None
            conn.execute("INSERT OR REPLACE INTO lease VALUES ('cricapi', ?, ?)",
                         (owner, self.clock() + 30))
        return owner

    def release(self, owner, backoff=2):
        with self.connection() as conn:
            conn.execute("UPDATE lease SET until=? WHERE provider='cricapi' AND owner=?",
                         (self.clock() + backoff, owner))
