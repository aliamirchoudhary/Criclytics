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
        with patch('criclytics_app.api.matches.completed_summaries', return_value=self.matches), \
             patch('criclytics_app.api.matches.completed_match', side_effect=lambda mid: next((m for m in self.matches if m['id'] == mid), None)), \
             patch('criclytics_app.api.matches.fetch_cricapi', return_value=None), \
             patch('criclytics_app.api.matches.load_live', return_value=None), \
             patch('criclytics_app.api.matches.augment_completed_match', side_effect=lambda m: m):
            response = client.get('/api/matches')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json['data']), 20)
            self.assertLess(len(response.data), 250 * 1024)
            self.assertIn('innings', client.get('/api/matches/1').json['data'])
            self.assertEqual(client.get('/api/matches?status=bad').status_code, 400)

    def test_search_matches_are_bounded_and_null_sort_is_safe(self):
        client = create_app({'TESTING': True, 'INITIALIZE_ENGINE': False,
                             'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''}).test_client()
        with patch('criclytics_app.api.players.load_processed', return_value={}), \
             patch('criclytics_app.api.players.completed_summaries', return_value=self.matches), \
             patch('criclytics_app.api.players.load_live', return_value=None):
            result = client.get('/api/search?q=Pakistan&limit=2')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(len(result.json['matches']), 2)
        players = {'Missing': {'name': 'Missing', 'batting': {'Test': {'average': None}}},
                   'Known': {'name': 'Known', 'batting': {'Test': {'average': 3}}}}
        with patch('criclytics_app.api.players.load_processed', return_value=players):
            result = client.get('/api/players?sort=avg')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json['players'][0]['name'], 'Known')
            self.assertIsNone(result.json['players'][1]['batting']['Test']['average'])
