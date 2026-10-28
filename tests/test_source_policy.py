import tempfile
import unittest
from unittest.mock import patch
from criclytics_app import create_app
from criclytics_app.integrations.source_policy import decision,require_source
from criclytics_app.services.legacy import fetch_cricapi


class PolicyTests(unittest.TestCase):
    def test_no_network_even_with_key_and_flag(self):
        self.assertEqual(decision()['network_collectors_allowed'],[])
        for source in ('cricapi','rapidapi','icc-rankings','unknown'):
            with self.assertRaises(RuntimeError):require_source(source)
        with tempfile.TemporaryDirectory() as directory:
            app=create_app({'LIVE_DIR':directory,'LIVE_FETCH_ENABLED':True,'REDIS_URL':'','CRICAPI_KEY':'test-only'})
            with app.app_context(),patch('requests.get') as upstream:
                self.assertIsNone(fetch_cricapi('matches',cache_file='matches.json'))
                upstream.assert_not_called()
                self.assertEqual(app.extensions['diagnostics'].snapshot()['events']['source_not_approved'],1)

    def test_legacy_cli_primitives_fail_before_network(self):
        from criclytics_app.integrations.live import cricapi_get
        from criclytics_app.integrations.matches import api_get
        from criclytics_app.integrations.rankings import fetch_rankings_json
        with patch('requests.get') as upstream:
            for call in (lambda:cricapi_get('matches'),lambda:api_get('/matches'),lambda:fetch_rankings_json('batting','T20I')):
                with self.assertRaises(RuntimeError):call()
            upstream.assert_not_called()
