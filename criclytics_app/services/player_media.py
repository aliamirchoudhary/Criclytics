"""Explicitly reviewed local portraits; no network fetch or fuzzy identity joins."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def load_catalog(manifest):
    if not manifest:
        return {}
    manifest = Path(manifest).resolve()
    if manifest.stat().st_size > 1024 * 1024:
        raise ValueError('Oversized media manifest')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or len(data.get('players', [])) > 1000:
        raise ValueError('Invalid media manifest')
    result = {}
    for item in data['players']:
        key = item['identity_id']
        if not re.fullmatch(r'player:cricsheet:[a-f0-9]{8}', key) or key in result:
            raise ValueError('Invalid or duplicate media identity')
        path = manifest.parent / item['file']
        if path.is_symlink() or not path.resolve().is_relative_to(manifest.parent) or not path.is_file():
            raise ValueError('Unsafe media path')
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError('Oversized portrait')
        raw = path.read_bytes()
        if not (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG\r\n\x1a\n')):
            raise ValueError('Portrait must be a PNG or JPEG image')
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Portrait hash mismatch')
        source = urlsplit(item.get('source', ''))
        if (source.scheme != 'https' or source.hostname not in ('h.cricapi.com', 'commons.wikimedia.org')
                or source.query or source.fragment or source.username or source.password):
            raise ValueError('Media source must be a reviewed key-free URL')
        if not item.get('source') or not item.get('use_scope'):
            raise ValueError('Portrait source/use review required')
        result[key] = {**item, 'path': path.resolve()}
    return result
