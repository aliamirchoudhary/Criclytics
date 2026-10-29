import io
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import requests
from criclytics_app import create_app
from criclytics_app.services.diagnostics import REQUIRED
from criclytics_app.services.json_io import atomic_json
from criclytics_app.services.legacy import fetch_cricapi


class DiagnosticTests(unittest.TestCase):
    def make_app(self, directory, **config):
        return create_app({'TESTING':True,'PROCESSED_DIR':directory,'LIVE_DIR':str(Path(directory)/'live'),'REDIS_URL':'','LIVE_FETCH_ENABLED':False,**config})

    def fill(self,directory):
        for name in REQUIRED:
            atomic_json(Path(directory)/name,{'data':[{'id':'one'}]} if name=='completed_matches.json' else {'fixture':{}})

    def test_readiness_missing_corrupt_and_optional_feed(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.make_app(directory); client=app.test_client()
            self.assertEqual(client.get('/api/health').status_code,200)
            self.assertEqual(client.get('/api/ready').status_code,503)
            self.fill(directory)
            response=client.get('/api/ready')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json['optional_feed']['state'],'degraded')
            self.assertIsNone(response.json['dataset_schema_version'])
            (Path(directory)/'players_index.json').write_text('corrupt')
            response=client.get('/api/ready')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json['required_artifacts']['players_index.json']['state'],'invalid')
            self.assertTrue(response.json['required_artifacts']['players_index.json']['last_good'])
            self.assertEqual(client.get('/api/status').status_code,503)

    def test_redacted_structured_logs_and_bounded_telemetry(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.make_app(directory,CRICAPI_KEY='secret-key',REDIS_URL='redis://private')
            capture=io.StringIO(); handler=logging.StreamHandler(capture)
            old=app.logger.level; app.logger.setLevel(logging.INFO);app.logger.addHandler(handler)
            try:
                response=app.test_client().get('/api/health?key=secret-query&note=private-coach-note')
            finally:
                app.logger.removeHandler(handler);app.logger.setLevel(old)
            log=capture.getvalue()
            self.assertIn('http_request',log)
            self.assertIn(response.headers['X-Request-ID'],log)
            for private in ('secret-key','secret-query','private-coach-note','redis://private'):
                self.assertNotIn(private,log)
            stats=app.extensions['diagnostics']
            for _ in range(1000):stats.observe(1,10,200)
            self.assertEqual(stats.snapshot()['recent_requests'],256)
            with self.assertRaises(ValueError):stats.event('arbitrary-unbounded-label')

    def test_distinct_cache_timeout_parse_quota_and_fallback_events(self):
        with tempfile.TemporaryDirectory() as directory:
            app=self.make_app(directory,LIVE_FETCH_ENABLED=True,CRICAPI_KEY='test-only')
            with app.app_context(),patch('criclytics_app.services.legacy.source_allowed',return_value=True):
                cache=app.extensions['live_cache'];stats=app.extensions['diagnostics']
                cache.write('matches.json',{'data':[]}); cache.read('matches.json')
                (Path(directory)/'live'/'broken.json').write_text('invalid')
                cache.read('broken.json')
                for error,event in ((requests.Timeout('https://x?key=private'),'provider_timeout'),(ValueError('private'),'provider_parse_failure')):
                    with patch.object(cache,'acquire',return_value='owner'),patch.object(cache,'release'),patch('requests.get',side_effect=error):
                        fetch_cricapi('matches',cache_file='matches.json',max_age_minutes=-1)
                    self.assertGreater(stats.snapshot()['events'][event],0)
                response=Mock(status_code=429);response.raise_for_status.side_effect=requests.HTTPError('private-url')
                with patch.object(cache,'acquire',return_value='owner'),patch.object(cache,'release'),patch('requests.get',return_value=response):
                    fetch_cricapi('matches',cache_file='matches.json',max_age_minutes=-1)
                events=stats.snapshot()['events']
                for event in ('quota_stop','cache_hit','cache_parse_failure','stale_fallback'):self.assertGreater(events[event],0)
