"""Runtime origin safety and static/Flask contract parity."""
import tempfile
import unittest
from pathlib import Path
from criclytics_app import create_app
from criclytics_app.frontend import api_base
from scripts.build_frontend import build


class RuntimeTests(unittest.TestCase):
    def test_invalid_origins_fail_closed(self):
        for value in ('http://example.com','https://user:secret@example.com','https://example.com/api','//example.com','https://example.com?key=x','https://example.com/#x','https://example.com:bad','https://exam\nple.com',"https://example.com;script-src"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                api_base(value)
        self.assertEqual(api_base('https://example.com/'),'https://example.com')
        self.assertEqual(api_base('http://127.0.0.1:5000'),'http://127.0.0.1:5000')

    def test_static_flask_parity_and_no_bootstrap(self):
        with tempfile.TemporaryDirectory() as directory:
            origin='https://backend.example.com'
            output=build(Path(directory)/'public', origin)
            app=create_app({'TESTING':True,'LIVE_DIR':str(Path(directory)/'live'),'REDIS_URL':'','LIVE_FETCH_ENABLED':False,'FRONTEND_API_BASE':origin})
            client=app.test_client()
            response=client.get('/static/js/runtime-config.js')
            self.assertEqual(response.text,(output/'static/js/runtime-config.js').read_text())
            self.assertIn('no-store',response.headers['Cache-Control'])
            for name in ('index.html','match-detail.html'):
                page=client.get('/'+name+'?id=1415755')
                self.assertEqual(page.data,(output/name).read_bytes())
                self.assertNotIn('__CRICLYTICS_MATCH_DETAIL__',page.text)
                self.assertIn("script-src 'self';",page.headers['Content-Security-Policy'])
                self.assertIn(origin,page.headers['Content-Security-Policy'])
                self.assertNotIn('Content-Security-Policy-Report-Only',page.headers)
                page.close()
            self.assertIn(origin,(output/'_headers').read_text())
