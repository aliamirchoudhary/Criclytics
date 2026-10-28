"""Response-contract diagnostic; failures return nonzero without a success banner."""
import argparse
import json

CHECKS = ('/api/matches', '/api/live', '/api/teams', '/api/venues', '/api/records',
          '/api/icc-rankings?category=batting&format=T20I', '/api/predict/status')


def verify(get):
    results = []
    for path in CHECKS:
        try:
            response = get(path)
            if response.status_code != 200:
                raise AssertionError('unexpected_status')
            data = response.get_json() if hasattr(response, 'get_json') else response.json()
            if not isinstance(data, dict) or 'error' in data:
                raise AssertionError('invalid_object')
            if path in ('/api/matches', '/api/live') and not isinstance(data.get('data'), list):
                raise AssertionError('invalid_match_array')
            if path == '/api/matches' and not isinstance(data.get('pagination'), dict):
                raise AssertionError('missing_pagination')
            if '/icc-rankings' in path and not isinstance(data.get('provenance'), dict):
                raise AssertionError('missing_provenance')
            if '/predict/' in path and (data.get('available') is not False or data.get('probability') is not None):
                raise AssertionError('unsupported_prediction')
            if not data:
                raise AssertionError('empty_dataset')
            results.append({'path': path, 'passed': True})
        except Exception as error:
            results.append({'path': path, 'passed': False, 'failure_type': type(error).__name__})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Explicit HTTP origin; defaults to in-process offline app')
    args = parser.parse_args()
    if args.base_url:
        import requests
        get = lambda path: requests.get(args.base_url.rstrip('/') + path, timeout=5)
    else:
        from criclytics_app import create_app
        get = create_app({'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''}).test_client().get
    results = verify(get)
    print(json.dumps({'checks': results, 'scope': 'Response contracts only; not production or model release sign-off.'}, indent=2))
    return 0 if all(row['passed'] for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
