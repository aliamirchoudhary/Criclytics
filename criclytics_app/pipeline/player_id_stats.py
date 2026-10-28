"""Non-overwriting, source-ID historical summaries; no serving promotion."""
import argparse
from collections import Counter
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import sqlite3

from . import cricsheet
from .aggregation import aggregate
from .artifacts import digest, validate
from .identities import local_id
from .schema import normalize_legacy_match, validate_match
from .scoring import score_match
from .rebuild import FORMATS
from ..paths import PACKAGE_ROOT, PROJECT_ROOT
from ..services.json_io import read_json, atomic_json


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def identity_match(raw, source_id):
    """Substitute identities before scoring, never merge already aggregated names."""
    match = deepcopy(raw)
    people = match['info'].get('registry', {}).get('people', {})
    names = {name: ('player:cricsheet:' + people[name] if name in people
                    else local_id('player', source_id, name))
             for roster in match['info']['players'].values() for name in roster}
    for roster in match['info']['players'].values():
        roster[:] = [names[name] for name in roster]
    for innings in match['innings']:
        for over in innings['overs']:
            for delivery in over['deliveries']:
                for field in ('batter', 'non_striker', 'bowler'):
                    delivery[field] = names[delivery[field]]
                for wicket in delivery.get('wickets', []):
                    wicket['player_out'] = names[wicket['player_out']]
                    for fielder in wicket.get('fielders', []):
                        if fielder.get('name') in names:
                            fielder['name'] = names[fielder['name']]
    return match


def export(tables, registry, destination):
    """Indexed summaries avoid loading all detailed profiles in a web process."""
    with contextlib.redirect_stdout(io.StringIO()):
        profiles = cricsheet.build_players_index(tables['bat'], tables['bowl'], include_bowling_only=True)
        yearly = cricsheet.build_player_yearly(tables['bat_year'])
        opponents = cricsheet.build_player_vs_opp(tables['bat_vs'])
        venues = cricsheet.build_player_venues(tables['bat_venue'])
        records = cricsheet.build_records(tables['bat'], tables['bowl'], [])
    entities = registry['entities']['player']
    if set(profiles) - set(entities):
        raise ValueError('Scored player absent from bound identity registry')
    with contextlib.closing(sqlite3.connect(destination)) as db, db:
        db.executescript('''
          CREATE TABLE players(id TEXT PRIMARY KEY, summary TEXT NOT NULL, profile TEXT NOT NULL);
          CREATE TABLE aliases(alias TEXT NOT NULL, id TEXT NOT NULL, PRIMARY KEY(alias,id));
          CREATE INDEX aliases_id ON aliases(id);
          CREATE TABLE metrics(id TEXT NOT NULL, format TEXT NOT NULL, runs REAL, wickets REAL,
            avg REAL, sr REAL, bat INTEGER, bowl INTEGER, PRIMARY KEY(id,format));
          CREATE TABLE memberships(id TEXT, team TEXT, PRIMARY KEY(id,team));
          CREATE TABLE documents(name TEXT PRIMARY KEY,payload TEXT NOT NULL);
        ''')
        for pid, entity in sorted(entities.items()):
            profile = profiles.get(pid, {'formats': [], 'batting': {}, 'bowling': {}, 'recent_form': []})
            profile.update(name=entity['name'], identity_id=pid, country=None,
                           observed_teams=entity['memberships'], aliases=entity['aliases'],
                           stats_available=bool(profile['formats']), dataset_id=registry['dataset_id'],
                           scope='Observed mens international subset; not complete careers')
            summary = deepcopy(profile)
            profile.update(yearly=yearly.get(pid, {}), vs_opp=opponents.get(pid, {}), at_venues=venues.get(pid, {}))
            db.execute('INSERT INTO players VALUES(?,?,?)', (pid, encoded(summary), encoded(profile)))
            for team in sorted({m['team_name'].casefold() for m in entity['memberships']}):
                db.execute('INSERT INTO memberships VALUES(?,?)', (pid, team))
            for fmt in profile['formats']:
                bat, bowl = profile['batting'].get(fmt, {}), profile['bowling'].get(fmt, {})
                db.execute('INSERT INTO metrics VALUES(?,?,?,?,?,?,?,?)',
                           (pid, fmt, bat.get('runs', 0), bowl.get('wickets', 0),
                            bat.get('average') or 0, bat.get('strike_rate') or 0, bool(bat), bool(bowl)))
        for alias, ids in sorted(registry['aliases']['player'].items()):
            for pid in ids:
                if pid in entities: db.execute('INSERT INTO aliases VALUES(?,?)', (alias, pid))
        for formats in records.values():
            for rows in formats.values():
                for row in rows:
                    pid = row['player']
                    row.update(player=entities[pid]['name'], identity_id=pid, country=None)
        db.execute('INSERT INTO documents VALUES(?,?)', ('records', encoded(records)))
        # The legacy venue tables intentionally span formats; keep that scope explicit.
        for kind, builder, table in [('batters', cricsheet.build_venue_batters, 'venue_bat'),
                                      ('bowlers', cricsheet.build_venue_bowlers, 'venue_bowl')]:
            with contextlib.redirect_stdout(io.StringIO()): rows_by_venue = builder(tables[table])
            for venue, rows in rows_by_venue.items():
                for row in rows:
                    pid = row['player']
                    if kind == 'batters':
                        original = tables[table][(venue, pid)]
                        row['average'] = cricsheet.avg(original['runs'], original['dismissals'])
                    row.update(player=entities[pid]['name'], identity_id=pid, country=None,
                               scope='Observed matches across formats')
                db.execute('INSERT INTO documents VALUES(?,?)', ('venue:'+kind+':'+venue, encoded(rows)))
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid candidate database')
    return {'rostered_identities': len(entities), 'scored_identities': len(profiles)}


def rebuild(raw_dir, parent, registry_path, output):
    raw_dir, output = Path(raw_dir).resolve(), Path(output).resolve()
    if output.exists() or any(output == p or output.is_relative_to(p) for p in
                             (raw_dir, PACKAGE_ROOT/'static', PROJECT_ROOT/'dist', PROJECT_ROOT/'data')):
        raise ValueError('Use a fresh private candidate outside source/data/public trees')
    parent_manifest = validate(parent)
    registry = read_json(registry_path)
    if registry.get('schema_version') != 1 or registry['dataset_id'] != parent_manifest['dataset_id']:
        raise ValueError('Registry/dataset mismatch')
    before = {p.name: digest(p) for p in (PROJECT_ROOT/'data/processed').glob('*.json')}
    tables = cricsheet.build_raw_accumulators([])
    totals = Counter()
    for entry in parent_manifest['inputs']:
        path = (raw_dir/entry['path']).resolve()
        if not path.is_relative_to(raw_dir) or digest(path) != entry['sha256']:
            raise ValueError('Raw source mismatch')
        raw = read_json(path)
        normalize_legacy_match(raw)
        validate_match(raw)
        match = identity_match(raw, path.stem)
        match['_format'], match['_file'] = FORMATS[path.parent.name], path.name
        match['_scored'] = score_match(match)
        for innings in match['_scored']['innings']:
            if innings['super_over']: continue
            for row in innings['batting']:
                totals['batting_runs'] += row['r']; totals['batting_innings'] += 1
            for row in innings['bowling']:
                totals['bowling_wickets'] += row['w']; totals['bowling_innings'] += 1
        aggregate([match], tables)
        totals['matches'] += 1
    for key, field, expected in [('bat','runs','batting_runs'), ('bat','innings','batting_innings'),
                                 ('bowl','wickets','bowling_wickets'), ('bowl','innings','bowling_innings')]:
        if sum(row[field] for row in tables[key].values()) != totals[expected]:
            raise ValueError('Canonical innings reconciliation failed')
    for group in ('bat_year', 'bat_vs', 'bat_venue'):
        if sum(row['runs'] for row in tables[group].values()) != totals['batting_runs']:
            raise ValueError('Context batting reconciliation failed')
    output.mkdir(parents=True)
    counts = export(tables, registry, output/'players.sqlite3')
    preserved = all(digest(PROJECT_ROOT/'data/processed'/name) == checksum for name, checksum in before.items())
    if not preserved: raise ValueError('Original artifacts changed')
    manifest = {'schema_version': 1, 'dataset_id': registry['dataset_id'],
                'registry_sha256': digest(registry_path), 'database_sha256': digest(output/'players.sqlite3'),
                'input_count': len(parent_manifest['inputs']), 'totals': dict(totals), **counts,
                'original_artifacts_unchanged': preserved,
                'code_sha256': {p.name: digest(p) for p in Path(__file__).parent.glob('*.py')},
                'attribution': registry['attribution'], 'promoted': False}
    atomic_json(output/'manifest.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=PROJECT_ROOT/'data/raw')
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(encoded(rebuild(args.raw_dir, args.parent, args.registry, args.output)))


if __name__ == '__main__': main()
