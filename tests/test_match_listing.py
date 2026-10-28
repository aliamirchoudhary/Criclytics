import unittest
from unittest.mock import patch

from criclytics_app import create_app
from criclytics_app.services.match_listing import listing


class MatchListingTests(unittest.TestCase):
    def setUp(self):
        self.matches = [dict(id=str(i), date='2026-01-01', teams=['Pakistan', 'India'],
                             matchType='T20', venue='Ground', innings=[{'private_detail': True}])
                        for i in range(27)]

    def test_stable_pagination_and_projection(self):
        ids = []
        for offset in (0, 10, 20):
            page = listing([], self.matches, {'offset': offset, 'limit': 10})
            ids.extend(m['id'] for m in page['data'])
            self.assertEqual(page['pagination']['total'], 27)
            self.assertTrue(all('innings' not in m for m in page['data']))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {str(i) for i in range(27)})

    def test_filters_and_duplicate_ids(self):
        page = listing([self.matches[0]], self.matches, {'team': 'PAK', 'format': 'T20I',
                                                        'status': 'completed', 'venue': 'Ground'})
        self.assertEqual(page['pagination']['total'], 26)
        self.assertEqual(listing([], self.matches, {'team': 'England'})['pagination']['total'], 0)

    def test_list_and_detail_api_contract(self):
        client = create_app({'TESTING': True, 'INITIALIZE_ENGINE': False,
                             'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''}).test_client()
        with patch('criclytics_app.api.routes.load_processed', return_value={'data': self.matches}), \
             patch('criclytics_app.api.routes.fetch_cricapi', return_value=None), \
             patch('criclytics_app.api.routes.load_live', return_value=None), \
             patch('criclytics_app.api.routes.augment_completed_match', side_effect=lambda m: m):
            response = client.get('/api/matches')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json['data']), 20)
            self.assertLess(len(response.data), 250 * 1024)
            self.assertIn('innings', client.get('/api/matches/1').json['data'])
            self.assertEqual(client.get('/api/matches?status=bad').status_code, 400)
