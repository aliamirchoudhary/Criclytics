from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from criclytics_app import create_app
from criclytics_app.services.provenance import metadata, merge_rankings
from criclytics_app.integrations.rankings import build_hardcoded_rankings


class ProvenanceTests(unittest.TestCase):
    def test_fallback_never_gets_new_observation_time(self):
        info = metadata(build_hardcoded_rankings())
        self.assertEqual(info['effective_date'], '2026-04')
        self.assertIsNone(info['fetched_at'])
        self.assertTrue(info['fallback'] and info['stale'])
        self.assertTrue(metadata({})['stale'])
        now = datetime(2026, 10, 28, tzinfo=timezone.utc)
        self.assertTrue(metadata({'source': 'manual', 'effective_date': '2026-04-01',
                                  'fetched_at': now.isoformat()}, now)['stale'])

    def test_partial_refresh_preserves_rows_and_dates(self):
        previous = {'source': 'old', 'fetched_at': '2025-01-01T00:00:00+00:00',
                    'team': {'ODI': [{'team': 'India'}]}, 'player': {}}
        incoming = {'team': {'ODI': [], 'Test': [{'team': 'Pakistan'}]}}
        info = {'source': 'permitted_import', 'effective_date': '2026-10-28',
                'fetched_at': '2026-10-28T00:00:00+00:00'}
        result = merge_rankings(previous, incoming, info)
        self.assertEqual(result['team']['ODI'], previous['team']['ODI'])
        self.assertEqual(result['category_metadata']['teams:ODI']['fetched_at'], previous['fetched_at'])
        self.assertEqual(result['category_metadata']['teams:Test'], info)

    def test_http_ranking_routes_never_refresh(self):
        app = create_app({'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': True, 'REDIS_URL': ''})
        with patch('requests.get', side_effect=AssertionError('No network allowed')), \
             patch('time.sleep', side_effect=AssertionError('No sleeping allowed')):
            response = app.test_client().get('/api/icc-rankings?category=teams&format=ODI')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json['provenance']['stale'])
            self.assertIsNone(response.json['provenance']['fetched_at'])
