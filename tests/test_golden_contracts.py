from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.rebuild import rebuild
from criclytics_app.pipeline.schema import validate_match, normalize_legacy_match, SchemaError
from criclytics_app.pipeline.scoring import score_match
from tools.final_verification import verify, CHECKS

PACK = json.loads((PROJECT_ROOT / 'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


class GoldenTests(unittest.TestCase):
    def test_hand_verified_totals_extras_and_retirement(self):
        for fixture in PACK['fixtures']:
            value = validate_match(deepcopy(fixture['match']))
            scored = score_match(value)['innings']
            self.assertEqual([i['total'] for i in scored], fixture['expected']['totals'])
            self.assertEqual([i['wickets'] for i in scored], fixture['expected']['wickets'])
        value = score_match(PACK['fixtures'][1]['match'])['innings'][0]
        self.assertEqual(value['batting'][0]['b'], 5)
        self.assertEqual(value['bowling'][0]['r'], 7)
        self.assertEqual(score_match(PACK['fixtures'][2]['match'])['innings'][0]['bowling'][0]['w'], 1)
        penalty = score_match(PACK['fixtures'][4]['match'])['innings'][0]
        self.assertEqual(penalty['total'], 8)
        self.assertTrue(penalty['fall_of_wickets'][0].startswith('3/1'))
        self.assertEqual(penalty['bowling'][0]['r'], 0)
        self.assertEqual(penalty['bowling'][0]['m'], 1)
        retired_out = deepcopy(PACK['fixtures'][2]['match'])
        retired_out['innings'][0]['overs'][0]['deliveries'][1]['wickets'][0]['kind'] = 'retired out'
        value = score_match(retired_out)['innings'][0]
        self.assertEqual((value['wickets'], value['bowling'][0]['w']), (2, 1))

    def test_malformed_and_unknown_fields_have_codes(self):
        original = PACK['fixtures'][1]['match']
        changes = [lambda m: m.update(secret_unknown='ignored'),
                   lambda m: m['meta'].update(data_version='99'),
                   lambda m: m['info']['players'].update({'Team A': 12}),
                   lambda m: m['info'].update(dates=['not-a-date']),
                   lambda m: m['innings'][0]['overs'][0]['deliveries'][0]['runs'].update(total=99),
                   lambda m: m['innings'][0]['overs'][0]['deliveries'][0]['extras'].update(magic=2),
                   lambda m: m['innings'][0]['overs'][0]['deliveries'][0]['runs'].update(total=True)]
        for change in changes:
            value = deepcopy(original)
            change(value)
            with self.assertRaises(SchemaError) as error:
                validate_match(value)
            self.assertTrue(error.exception.code)
            self.assertTrue(error.exception.location)

    def test_narrow_legacy_normalization_and_real_penalty_keys(self):
        value = deepcopy(PACK['fixtures'][0]['match'])
        value['innings'][0]['miscounted_overs'] = {'0': {'balls': '6'}}
        changes = normalize_legacy_match(value)
        self.assertEqual(len(changes), 1)
        self.assertEqual(value['innings'][0]['miscounted_overs']['0']['balls'], 6)
        validate_match(value)
        value['innings'][0]['penalty_runs'] = {'before': 5}
        with self.assertRaises(SchemaError):
            validate_match(value)

    def test_deterministic_rebuild_and_api_nesting(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            folders = {'Test': 'tests_male_json', 'T20': 't20s_male_json', 'ODI': 'odis_male_json'}
            for fixture in PACK['fixtures']:
                path = root / 'raw' / folders[fixture['match']['info']['match_type']] / (fixture['id'] + '.json')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(fixture['match']), encoding='utf-8')
            corrupt = root / 'raw/odis_male_json/corrupt.json'
            corrupt.write_text('{"unexpected": true}', encoding='utf-8')
            first, second = root / 'first', root / 'second'
            report = rebuild(root / 'raw', first)
            rebuild(root / 'raw', second)
            self.assertEqual(report['rejected'][0]['code'], 'unknown_field')
            for path in first.glob('*.json'):
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')),
                                 json.loads((second / path.name).read_text(encoding='utf-8')), path.name)
            with self.assertRaises(ValueError):
                rebuild(root / 'raw', first)
            app = create_app({'PROCESSED_DIR': first, 'LIVE_DIR': root / 'live',
                              'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
            client = app.test_client()
            a = client.get('/api/players/A').json
            self.assertEqual((a['batting']['Test']['innings'], a['batting']['Test']['highest'],
                              a['batting']['Test']['fifties'], a['batting']['Test']['hundreds']), (2, 60, 2, 0))
            self.assertEqual(a['batting']['T20I']['runs'], 5)
            self.assertEqual(client.get('/api/h2h?team_a=Team%20X&team_b=Team%20A&format=Test').json['draws'], 1)
            self.assertEqual(client.get('/api/matches?status=completed').json['pagination']['total'], len(PACK['fixtures']))
            self.assertEqual(client.get('/api/matches/t20-tie-super').json['data']['innings'][2]['super_over'], True)
            venue = client.get('/api/venues/Fictional%20Ground').json
            self.assertIsNone(venue['test']['chase_win_pct'])

    def test_diagnostic_cannot_report_success_after_failure(self):
        failed = Mock(status_code=500)
        failed.json.return_value = {'data': []}
        results = verify(lambda path: failed)
        self.assertEqual(len(results), len(CHECKS))
        self.assertFalse(any(row['passed'] for row in results))
