import unittest
from unittest.mock import Mock
from criclytics_app import create_app
from criclytics_app.ml.probability import ProbabilityEngine


class PredictionBoundaryTests(unittest.TestCase):
    def test_cook_missing_and_schema_variations_never_invent_scores(self):
        engine = ProbabilityEngine('nonexistent')
        for name in ('SC Cook', 'Unknown'):
            for metric in ('50', '100', 'wicket_maiden', 'strike_rate>140', 'avg>50'):
                value = engine.player_performance_likelihood(name, metric, 'Test')
                self.assertFalse(value['available'])
                self.assertIsNone(value['probability'])
                self.assertIsNone(value['confidence'])
                self.assertIsNone(value['sample_count'])
        # H2H/team/venue schema mismatches cannot be hidden behind fabricated defaults.
        self.assertFalse(engine.team_match_outcome('India', 'Pakistan')['available'])
        self.assertFalse(engine.venue_performance_bias('Lords')['available'])
        board = engine.leaderboard_predictions()
        self.assertEqual(board['predictions'], [])
        self.assertEqual(board['evaluated_players'], 0)

    def test_every_prediction_route_is_contained_even_if_engine_injected(self):
        app = create_app({'TESTING': True, 'INITIALIZE_ENGINE': True,
                          'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
        engine = Mock()
        app.extensions['probability_engine'] = engine
        client = app.test_client()
        for path in ('player/SC%20Cook?format=Test&metric=100', 'player/Unknown/all',
                     'venue/Lords?format=Test', 'leaderboard?limit=500', 'status'):
            response = client.get('/api/predict/' + path)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json['available'])
            self.assertIsNone(response.json['probability'])
            self.assertEqual(response.json['kind'], 'unavailable')
        response = client.post('/api/predict/team_match', json={'team_a': 'India', 'team_b': 'Pakistan'})
        self.assertFalse(response.json['available'])
        self.assertEqual(engine.mock_calls, [])
