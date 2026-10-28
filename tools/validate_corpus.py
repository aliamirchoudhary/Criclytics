"""Read-only schema audit; emit quarantined-input codes without changing source files."""
import argparse
from collections import Counter
import json
from pathlib import Path
from criclytics_app.pipeline.schema import SchemaError, validate_match, normalize_legacy_match
from criclytics_app.services.json_io import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    accepted, rejected, normalized = 0, [], []
    for path in sorted(args.raw_dir.glob('*_male_json/*.json')):
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            changes = normalize_legacy_match(value)
            if changes:
                normalized.append({'path': path.relative_to(args.raw_dir).as_posix(), 'changes': changes})
            validate_match(value)
            accepted += 1
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            rejected.append({'path': path.relative_to(args.raw_dir).as_posix(),
                             'code': error.code if isinstance(error, SchemaError) else type(error).__name__,
                             'location': error.location if isinstance(error, SchemaError) else 'match'})
    atomic_json(args.report, {'accepted': accepted, 'rejected': rejected, 'normalizations': normalized,
                             'rejection_counts': dict(Counter(row['code'] for row in rejected))})
    print(json.dumps({'accepted': accepted, 'rejected': len(rejected)}))
    return 1 if rejected else 0


if __name__ == '__main__':
    raise SystemExit(main())
