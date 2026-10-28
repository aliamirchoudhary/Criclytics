"""Streaming, non-overwriting v2 rebuild with input/output hashes and difference report."""
import argparse
from collections import Counter
import gc
import contextlib
import io
import hashlib
import json
from pathlib import Path

from ..paths import PROJECT_ROOT
from ..services.live_cache import atomic_json
from . import cricsheet as legacy
from .aggregation import aggregate

FORMATS = {'tests_male_json': 'Test', 'odis_male_json': 'ODI', 't20s_male_json': 'T20I'}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def rebuild(raw_dir, output, previous=None, limit=None):
    raw_dir, output = Path(raw_dir).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(raw_dir):
        raise ValueError('Use a fresh output directory outside the raw source tree')
    previous = Path(previous).resolve() if previous else None
    before = {p.name: digest(p) for p in sorted(previous.glob('*.json'))} if previous else {}
    output.mkdir(parents=True)
    code_hashes = {p.name: digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))}
    inputs, rejected, completed = [], [], []
    accumulators = legacy.build_raw_accumulators([])
    outcomes = Counter()
    paths = [(p, fmt) for folder, fmt in FORMATS.items() for p in sorted((raw_dir / folder).glob('*.json'))]
    if limit is not None:
        paths = paths[:limit]
    for path, fmt in paths:
        record = {'path': path.relative_to(raw_dir).as_posix(), 'sha256': digest(path)}
        inputs.append(record)
        try:
            match = json.loads(path.read_text(encoding='utf-8'))
            info = match['info']
            if info.get('team_type') != 'international' or info.get('gender') != 'male':
                raise ValueError('Outside declared international male scope')
            if len(info['teams']) != 2 or not info['dates'] or not info.get('outcome'):
                raise ValueError('Missing match identity/date/outcome')
            match['_format'], match['_file'] = fmt, path.name
            # Validate the full score before modifying any accumulator.
            from .scoring import score_match
            match['_scored'] = score_match(match)
        except (KeyError, ValueError, TypeError, AttributeError) as error:
            rejected.append({**record, 'reason_type': type(error).__name__})
            continue
        # Unexpected aggregation/export failures abort the candidate, never skip a
        # partially accumulated match and silently publish inconsistent totals.
        aggregate([match], accumulators)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            completed.extend(legacy.build_completed_matches([match]))
        outcomes[info['outcome'].get('result') or 'win'] += 1
    if not completed:
        raise ValueError('No valid matches; incomplete candidate is not publishable')
    old_output = legacy.OUT_DIR
    try:
        legacy.OUT_DIR = str(output)
        legacy.save_all(accumulators, [])
    finally:
        legacy.OUT_DIR = old_output
    atomic_json(output / 'completed_matches.json', {'schema_version': '2.0', 'data': completed})
    count = len(completed)
    del completed
    gc.collect()
    current = json.loads((output / 'players_index.json').read_text(encoding='utf-8'))
    old_players = json.loads((previous / 'players_index.json').read_text(encoding='utf-8')) if previous and (previous / 'players_index.json').exists() else {}
    differences = Counter()
    examples = []
    for name, player in current.items():
        old = old_players.get(name, {})
        for kind in ('batting', 'bowling'):
            for fmt, stats in player[kind].items():
                for field, value in stats.items():
                    old_value = old.get(kind, {}).get(fmt, {}).get(field)
                    if old_value != value:
                        differences[kind + '.' + field] += 1
                        if name == 'SC Cook' or len(examples) < 12:
                            examples.append({'player': name, 'format': fmt, 'kind': kind,
                                             'field': field, 'before': old_value, 'after': value})
    preserved = not previous or all(digest(previous / name) == value for name, value in before.items())
    if not preserved:
        raise RuntimeError('Original artifact preservation check failed')
    report = {'schema_version': '2.0', 'scope': 'local mens international subset; not complete careers',
              'inputs': len(inputs), 'accepted_matches': count, 'rejected': rejected,
              'outcomes': dict(outcomes), 'players_before': len(old_players), 'players_after': len(current),
              'changed_player_format_fields': dict(differences), 'examples': examples,
              'original_artifacts_unchanged': preserved, 'subset_limit': limit,
              'notes': ['Innings identities replace match-total batting approximation.',
                        'No-ball BF and legal bowling balls differ; byes/leg-byes/penalties excluded from bowler runs.',
                        'Regulation totals exclude super overs; draws/ties/no-results remain distinct.',
                        'Candidate is not automatically promoted to serving.']}
    atomic_json(output / 'difference_report.json', report)
    manifest = {'schema_version': '2.0', 'scoring_contract': 'docs/SCORING_CONTRACT.md',
                'inputs': inputs, 'original_artifacts': before,
                'code_sha256': code_hashes,
                'outputs': {p.name: digest(p) for p in sorted(output.glob('*.json'))}}
    atomic_json(output / 'manifest.json', manifest)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=PROJECT_ROOT / 'data/raw')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous', type=Path, default=PROJECT_ROOT / 'data/processed')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('limit must be positive')
    print(json.dumps(rebuild(args.raw_dir, args.output, args.previous, args.limit), indent=2))


if __name__ == '__main__':
    main()
