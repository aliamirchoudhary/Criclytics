"""Public-media boundaries, isolated live widget and local session discovery."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

from criclytics_app import create_app
from criclytics_app.services.player_media import load_catalog
from scripts.build_frontend import build


class CricketExperienceTests(unittest.TestCase):
    def app(self, root, **config):
        return create_app({'TESTING': True, 'LIVE_DIR': root/'live', 'REDIS_URL': '',
                           'LIVE_FETCH_ENABLED': False, 'IDENTITY_REGISTRY': '',
                           'IDENTITY_PLAYER_STORE': '', 'PLAYER_MEDIA_MANIFEST': '',
                           'EXPERIMENTAL_FORECASTS': False, **config})

    def test_media_allowlist_hash_and_source_not_a_private_file_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'\xff\xd8\xff' + b'fictional-image-fixture'
            (root/'portrait.jpg').write_bytes(raw)
            entry = {'identity_id': 'player:cricsheet:1234abcd', 'name': 'Fixture Player',
                     'file': 'portrait.jpg', 'sha256': hashlib.sha256(raw).hexdigest(),
                     'source': 'https://h.cricapi.com/img/players/fixture.jpg',
                     'use_scope': 'Authored test fixture, not a real player image'}
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps({'schema_version': 1, 'players': [entry]}))
            client = self.app(root, PLAYER_MEDIA_MANIFEST=manifest).test_client()
            catalog = client.get('/api/player-media').json
            self.assertTrue(catalog['available'])
            self.assertNotIn('path', catalog['players'][0])
            self.assertEqual(client.get(catalog['players'][0]['image_path']).data, raw)
            self.assertEqual(client.get('/api/player-media/no-such-player').status_code, 404)
            for key, value in [('file', '../.env'), ('sha256', 'bad'),
                               ('source', 'https://h.cricapi.com/img/players/test?apikey=secret'),
                               ('identity_id', 'arbitrary-display-name')]:
                broken = {**entry, key: value}
                manifest.write_text(json.dumps({'schema_version': 1, 'players': [broken]}))
                with self.assertRaises(ValueError):
                    load_catalog(manifest)
            self.assertEqual(client.get('/.env').status_code, 404)

    def test_widget_is_opt_in_sandbox_document_and_main_csp_stays_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = self.app(root).test_client()
            self.assertFalse(client.get('/api/player-media').json['available'])
            home = client.get('/')
            self.assertIn("script-src 'self'", home.headers['Content-Security-Policy'])
            self.assertIn("script-src-attr 'none'", home.headers['Content-Security-Policy'])
            self.assertIn('frame-src https://cwidget.crictimes.org', home.headers['Content-Security-Policy'])
            self.assertEqual(client.get('/static/widgets/live-scores.html').status_code, 404)
            output = build(root/'frontend', api_origin='https://backend.example')
            self.assertNotIn('! Content-Security-Policy', (output/'_headers').read_text())
            self.assertIn('https://backend.example', (output/'_headers').read_text())

    def test_session_directory_reuses_local_privacy_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = self.app(root)
            client = app.test_client()
            self.assertEqual(client.get('/api/v1/workspaces').json['workspaces'], [])
            source = root/'events.sqlite3'
            with sqlite3.connect(source) as db:
                db.execute('CREATE TABLE matches(match_id TEXT,payload TEXT)')
                db.execute('INSERT INTO matches VALUES(?,?)', ('match:manual:fixture', json.dumps({
                    'teams': ['A', 'B'], 'format': 'T20I', 'dates': ['2026-01-01'],
                    'source_hash': 'not_public_metadata'})))
            db.close()
            app.extensions['forecast_service'] = SimpleNamespace(source=source)
            result = client.get('/api/v1/workspaces')
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json['workspaces'][0]['teams'], ['A', 'B'])
            self.assertNotIn('source_hash', result.json['workspaces'][0])
            self.assertEqual(result.headers['Cache-Control'], 'no-store, private')
            self.assertEqual(client.get('/api/v1/workspaces', headers={'Host':'attacker.example'}).status_code, 403)
            self.assertEqual(client.get('/api/v1/workspaces', environ_base={'REMOTE_ADDR':'8.8.8.8'}).status_code, 403)
            self.assertEqual(client.get('/api/v1/workspaces', headers={'Origin':'https://attacker.example'}).status_code, 403)
