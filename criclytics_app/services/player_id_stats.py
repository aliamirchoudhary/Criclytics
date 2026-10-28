"""Read-only, bounded queries against an explicitly selected identity candidate."""
import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from werkzeug.exceptions import Conflict, BadRequest
from .json_io import read_json
from ..pipeline.artifacts import digest


class PlayerStore:
    def __init__(self, directory, dataset_id, registry_hash):
        directory = Path(directory).resolve()
        from ..paths import PACKAGE_ROOT, PROJECT_ROOT
        if any(directory == public or directory.is_relative_to(public) for public in
               (PACKAGE_ROOT/'static', PROJECT_ROOT/'dist')):
            raise ValueError('Player candidate must be outside public output')
        self.path = directory/'players.sqlite3'
        self.manifest = read_json(directory/'manifest.json')
        if (self.manifest.get('schema_version') != 1 or self.manifest.get('dataset_id') != dataset_id
                or self.manifest.get('registry_sha256') != registry_hash
                or self.path.is_symlink() or digest(self.path) != self.manifest.get('database_sha256')):
            raise ValueError('Player candidate must match selected dataset, registry and database hash')
        with self.connect() as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Invalid player candidate')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path.as_uri()+'?mode=ro', uri=True)
        try: yield db
        finally: db.close()

    def profile(self, value):
        with self.connect() as db:
            row = db.execute('SELECT profile FROM players WHERE id=?', (value,)).fetchone()
            if row: return json.loads(row[0])
            ids = db.execute('SELECT id FROM aliases WHERE alias=? LIMIT 2', (str(value).strip().casefold(),)).fetchall()
            if len(ids) > 1: raise Conflict('Ambiguous player name; search players and choose a stable identity')
            if not ids: return None
            return json.loads(db.execute('SELECT profile FROM players WHERE id=?', ids[0]).fetchone()[0])

    def listing(self, args):
        fmt, role = args.get('format'), args.get('role', 'all')
        metric = args.get('sort', 'runs')
        if metric not in ('runs', 'wickets', 'avg', 'sr'): raise BadRequest('Unsupported metric')
        limit, offset = int(args.get('limit', 50)), int(args.get('offset', 0))
        if not 1 <= limit <= 500 or not 0 <= offset <= 100000: raise ValueError('Invalid pagination')
        clauses, params = [], []
        q = args.get('search', '').strip().casefold()
        team = args.get('country', '').strip().casefold()
        if q:
            clauses.append('EXISTS(SELECT 1 FROM aliases a WHERE a.id=p.id AND instr(a.alias,?)>0)')
            params.append(q)
        if team:
            clauses.append('EXISTS(SELECT 1 FROM memberships t WHERE t.id=p.id AND instr(t.team,?)>0)')
            params.append(team)
        conditions, metric_params = [], []
        if fmt: conditions.append('m.format=?'); metric_params.append(fmt)
        if role in ('bat', 'bowl'): conditions.append('m.'+role+'=1')
        if conditions:
            clauses.append('EXISTS(SELECT 1 FROM metrics m WHERE m.id=p.id AND '+' AND '.join(conditions)+')')
            params.extend(metric_params)
        where = ' WHERE '+' AND '.join(clauses) if clauses else ''
        aggregate = 'MAX' if metric in ('avg', 'sr') else 'SUM'
        score = f'(SELECT {aggregate}(m.{metric}) FROM metrics m WHERE m.id=p.id'+(' AND m.format=?' if fmt else '')+')'
        with self.connect() as db:
            total = db.execute('SELECT COUNT(*) FROM players p'+where, params).fetchone()[0]
            rows = db.execute('SELECT p.summary FROM players p'+where+' ORDER BY COALESCE('+score+',0) DESC,p.id LIMIT ? OFFSET ?',
                              params+([fmt] if fmt else [])+[limit, offset]).fetchall()
        return {'total': total, 'offset': offset, 'limit': limit, 'players': [json.loads(r[0]) for r in rows],
                'identity_correct': True, 'membership_filter': 'country filters observed teams, not nationality',
                'dataset_id': self.manifest['dataset_id']}

    def records(self):
        with self.connect() as db:
            return json.loads(db.execute('SELECT payload FROM documents WHERE name=?', ('records',)).fetchone()[0])

    def document(self, name):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM documents WHERE name=?', (name,)).fetchone()
            return json.loads(row[0]) if row else {}

    def rankings(self, fmt, kind, limit):
        if kind not in ('batting', 'bowling'): raise BadRequest('Unsupported ranking type')
        # Bounded SQL result before profiles are decoded, including the legacy minimum sample.
        key, minimum = ('innings', 5) if kind == 'batting' else ('wickets', 5)
        score = 'runs' if kind == 'batting' else 'wickets'
        with self.connect() as db:
            rows = db.execute('SELECT summary FROM players p JOIN metrics m ON p.id=m.id WHERE m.format=? '
                              'AND json_extract(p.summary,?)>=? ORDER BY m.'+score+' DESC,p.id LIMIT ?',
                              (fmt, '$.'+kind+'.'+fmt+'.'+key, minimum, limit)).fetchall()
        return [{**p[kind][fmt], 'player': p['name'], 'identity_id': p['identity_id']}
                for p in map(lambda r: json.loads(r[0]), rows)]


def initialize(app):
    app.extensions['player_id_store'] = None
    if not app.config['IDENTITY_PLAYER_STORE']: return
    registry = app.extensions['identity_registry'].data
    if not registry: raise ValueError('Identity player candidate requires a bound registry')
    app.extensions['player_id_store'] = PlayerStore(app.config['IDENTITY_PLAYER_STORE'], registry['dataset_id'],
                                                   digest(app.config['IDENTITY_REGISTRY']))
