"""Regressions for actual boundary failures found in the pre-plan audit."""
import contextlib
import importlib
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from criclytics_app import create_app
from criclytics_app.services import legacy
from scripts.verify_backend_inventory import unexpected_files


class AuditRemediationTests(unittest.TestCase):
    def test_provider_errors_never_log_synthetic_credentials_or_urls(self):
        import requests
        from criclytics_app.integrations import live, matches
        secret = 'AUDIT_SYNTHETIC_KEY'
        private_url = 'https://provider.invalid/?apikey=' + secret
        capture = io.StringIO()
        with patch('criclytics_app.integrations.source_policy.require_source'), \
                patch.object(live, 'CRICAPI_KEY', secret), \
                patch('requests.get', side_effect=requests.RequestException(private_url)), \
                contextlib.redirect_stdout(capture):
            self.assertIsNone(live.cricapi_get('currentMatches'))
            self.assertIsNone(matches.api_get('/synthetic-path'))
        self.assertNotIn(secret,capture.getvalue())
        self.assertNotIn('https://',capture.getvalue())
        self.assertIn('RequestException',capture.getvalue())

    def test_photo_helpers_cannot_rewrite_metadata(self):
        from criclytics_app.integrations import live
        with patch('requests.get') as get:
            for function,args in ((live.fetch_player_photo, 'fictional'),
                                  (live.fetch_photos_for_players, ['fictional'])):
                with self.assertRaises(RuntimeError):
                    function(args)
            get.assert_not_called()

    def test_retired_entrypoints_have_no_network_or_pickle_side_effects(self):
        for name in ('integrations.schedule', 'integrations.photos', 'ml.training', 'ml.legacy_probability'):
            with self.subTest(module=name), patch('urllib.request.urlopen') as urlopen, \
                    patch('requests.get') as get, patch('pickle.load') as load:
                module = importlib.import_module('criclytics_app.' + name)
                capture = io.StringIO()
                with contextlib.redirect_stdout(capture), self.assertRaises(SystemExit):
                    module.main()
                urlopen.assert_not_called()
                get.assert_not_called()
                load.assert_not_called()
                self.assertEqual(capture.getvalue(), '')

    def test_missing_selected_artifact_and_match_never_cross_generations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, old = root/'selected', root/'old'
            selected.mkdir()
            old.mkdir()
            (old/'records.json').write_text('{"old_generation":true}')
            (old/'completed_matches.json').write_text('{"data":[{"id":"old"}]}')
            app = create_app({'TESTING':True, 'PROCESSED_DIR':str(selected),
                              'DATASET_STORE':'', 'LIVE_DIR':str(root/'live'), 'REDIS_URL':''})
            with app.app_context(), patch.object(legacy, 'BASE_DIR', str(old)):
                self.assertIsNone(legacy.load_processed('records.json'))
                self.assertIsNone(legacy.completed_match('old'))
                self.assertEqual(legacy.completed_summaries(), [])

    def test_default_is_unselected_and_archive_requires_explicit_opt_in(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'PROCESSED_DIR':'', 'DATASET_STORE':'', 'LEGACY_DATA_ENABLED':'0'}):
            config = {'TESTING':True,'LIVE_DIR':directory,'REDIS_URL':''}
            app = create_app(config)
            self.assertEqual(app.config['DATA_SELECTION_MODE'], 'unselected')
            self.assertEqual(Path(app.config['PROCESSED_DIR']).name, 'unselected')
            self.assertEqual(app.test_client().get('/api/ready').status_code, 503)
            archive = create_app({**config, 'LEGACY_DATA_ENABLED':True})
            self.assertEqual(archive.config['DATA_SELECTION_MODE'], 'legacy_archive_opt_in')
            self.assertEqual(Path(archive.config['PROCESSED_DIR']).name, 'processed')

    def test_readiness_reports_loaded_features_without_issuing_or_disclosing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = create_app({'TESTING':True,'PROCESSED_DIR':directory,'DATASET_STORE':'',
                              'LIVE_DIR':str(root/'live'),'REDIS_URL':''})
            app.extensions['scenario_model'] = SimpleNamespace(identity='scenario-test-id')
            app.extensions['forecast_service'] = SimpleNamespace(
                model_id='forecast-test-id',source=root/'private-source',ledger=root/'private-ledger')
            response = app.test_client().get('/api/ready')
            self.assertEqual(response.status_code, 503)  # Missing history remains independent.
            self.assertTrue(response.json['scenarios']['available'])
            self.assertTrue(response.json['issued_forecasts']['available'])
            self.assertTrue(response.json['model']['available'])
            self.assertIsNone(response.json['issued_forecasts']['current_forecast_eligible'])
            self.assertNotIn('workers', response.json['limits'])
            self.assertNotIn('private-source', response.get_data(as_text=True))

    def test_remote_inventory_fails_closed_without_deleting_anything(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'wsgi.py').write_text('fixture')
            self.assertEqual(unexpected_files(['wsgi.py','.gitattributes'],root), set())
            self.assertEqual(unexpected_files(['wsgi.py','.env','old/model.pkl'],root),
                             {'.env','old/model.pkl'})

    def test_staging_excludes_private_files_even_inside_allowed_trees(self):
        from scripts import stage_backend
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root/'checkout'
            (checkout/'criclytics_app').mkdir(parents=True)
            (checkout/'data/static').mkdir(parents=True)
            for name in ('app.py','wsgi.py','requirements.txt','Dockerfile','.dockerignore','README.md'):
                (checkout/name).write_text('fixture')
            for tree in ('criclytics_app','data/static'):
                for name in ('visible.json','.env','.env.local','secret.env','model.pkl','private.sqlite3'):
                    (checkout/tree/name).write_text('synthetic fixture')
            with patch.object(stage_backend,'PROJECT_ROOT',checkout):
                output = stage_backend.stage(root/'backend')
            for tree in ('criclytics_app','data/static'):
                self.assertEqual({p.name for p in (output/tree).iterdir()}, {'visible.json'})

    def test_retired_public_assets_are_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app({'TESTING':True,'LIVE_DIR':directory,'REDIS_URL':''})
            for path in ('/cricklytics.js','/styles.css','/static/js/compare-api.js'):
                self.assertEqual(app.test_client().get(path).status_code,404)
