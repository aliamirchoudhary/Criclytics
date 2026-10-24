"""Offline regression checks for the migration and public-file boundary."""
import hashlib
import json
import os
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from criclytics_app import create_app
from criclytics_app.paths import PACKAGE_ROOT, PROJECT_ROOT
from criclytics_app.services.legacy import render_match_detail_bootstrap
from criclytics_app.web.routes import PAGES
from scripts.build_frontend import build
from scripts.stage_backend import stage


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = "href" if tag == "link" else "src"
        if tag in {"link", "script", "img"} and attrs.get(key):
            self.urls.append(attrs[key])


class StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.app = create_app({"TESTING": True, "LIVE_FETCH_ENABLED": False,
                              "REDIS_URL": "", "LIVE_DIR": cls.temp.name,
                              "INITIALIZE_ENGINE": False})
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_private_files_never_served(self):
        for path in ["/.env", "/.git/HEAD", "/app.py", "/wsgi.py", "/requirements.txt",
                     "/data/static/players_meta.json", "/data/processed/completed_matches.json",
                     "/criclytics_app/__init__.py", "/static/../services/legacy.py",
                     "/static/%2e%2e/%2e%2e/.env"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_all_pages_and_referenced_local_assets(self):
        for page in sorted(PAGES):
            with self.subTest(page=page):
                response = self.client.get("/" + page)
                self.assertEqual(response.status_code, 200)
                parser = Assets()
                parser.feed(response.get_data(as_text=True))
                for url in parser.urls:
                    if not url.startswith(("https:", "http:", "data:", "//", "#")):
                        self.assertTrue(url.startswith("/static/"), url)
                        with self.client.get(url) as asset_response:
                            self.assertEqual(asset_response.status_code, 200, url)
                response.close()

    def test_api_paths_and_methods_preserved(self):
        baseline = json.loads((PROJECT_ROOT / "tests/fixtures/legacy_routes.json").read_text())
        actual = {r.rule: r.methods for r in self.app.url_map.iter_rules()}
        for item in baseline:
            if item["path"].startswith("/api/"):
                self.assertIn(item["path"], actual)
                self.assertTrue(set(item["methods"]) <= actual[item["path"]])

    def test_no_live_fetch_when_offline(self):
        with patch("requests.get", side_effect=AssertionError("Unexpected upstream request")):
            for path in ["/api/live", "/api/series", "/api/matches/unknown", "/api/matches/unknown/score",
                         "/api/icc-rankings?category=teams&format=T20I"]:
                self.assertIn(self.client.get(path).status_code, [200, 404])

    def test_cors_allowlist(self):
        good = self.client.get("/api/status", headers={"Origin": "https://criclytics.aliamirchoudhary.workers.dev"})
        bad = self.client.get("/api/status", headers={"Origin": "https://untrusted.example"})
        self.assertEqual(good.headers.get("Access-Control-Allow-Origin"), "https://criclytics.aliamirchoudhary.workers.dev")
        self.assertNotIn("Access-Control-Allow-Origin", bad.headers)

    def test_bootstrap_cannot_close_script(self):
        html = render_match_detail_bootstrap({"name": "</script><img src=x onerror=alert(1)>"})
        self.assertEqual(html.lower().count("</script>"), 1)
        self.assertNotIn("<img src=x", html)
        self.assertIn(r"\u003c/script\u003e", html)

    def test_factory_and_data_paths_survive_different_cwd(self):
        old = os.getcwd()
        try:
            os.chdir(self.temp.name)
            app = create_app({"TESTING": True, "INITIALIZE_ENGINE": False,
                              "LIVE_FETCH_ENABLED": False, "REDIS_URL": ""})
            with app.test_client().get("/") as response:
                self.assertEqual(response.status_code, 200)
            self.assertEqual(app.config["PROCESSED_DIR"], str(PROJECT_ROOT / "data/processed"))
        finally:
            os.chdir(old)

    def test_static_build_contains_only_public_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = build(directory)
            self.assertEqual({p.name for p in target.glob("*.html")}, PAGES)
            self.assertTrue((target / "static/js/cricklytics.js").is_file())
            self.assertFalse(list(target.rglob("*.py")))
            self.assertFalse(list(target.rglob(".env")))

    def test_static_build_refuses_unknown_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            unexpected = Path(directory) / ".env"
            unexpected.write_text("test marker", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                build(directory)
            self.assertEqual(unexpected.read_text(), "test marker")

    def test_backend_upload_is_allowlisted(self):
        with tempfile.TemporaryDirectory() as directory:
            output = stage(Path(directory) / "backend")
            self.assertTrue((output / "wsgi.py").is_file())
            self.assertTrue((output / "criclytics_app/api/routes.py").is_file())
            self.assertEqual({p.name for p in output.iterdir()}, {
                "app.py", "wsgi.py", "requirements.txt", "Dockerfile", ".dockerignore",
                "README.md", "criclytics_app", "data",
            })
            self.assertFalse(list(output.rglob(".env")))
            self.assertFalse(list(output.rglob("*.pkl")))
            self.assertFalse(list(output.rglob("*.pyc")))
            self.assertEqual({p.name for p in (output / "data").iterdir()}, {"static"})

    def test_legacy_public_asset_urls_redirect(self):
        for name in ["styles.css", "cricklytics.js", "logo-icon.png"]:
            with self.client.get("/" + name, follow_redirects=True) as response:
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.request.path.startswith("/static/"))


@unittest.skipUnless(os.getenv("CRICLYTICS_FULL_DATA_TESTS") == "1", "Opt in with local legacy data")
class LocalDataRegressionTests(unittest.TestCase):
    def test_captured_api_responses_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app({"TESTING": True, "LIVE_FETCH_ENABLED": False, "REDIS_URL": ""})
            baseline = json.loads((PROJECT_ROOT / "tests/fixtures/legacy_responses.json").read_text())
            with patch("requests.get", side_effect=AssertionError("Unexpected upstream request")):
                for path, expected in baseline.items():
                    with self.subTest(path=path):
                        r = app.test_client().get(path)
                        self.assertEqual(r.status_code, expected["status"])
                        digest = hashlib.sha256(json.dumps(r.get_json(), sort_keys=True).encode()).hexdigest()
                        self.assertEqual(digest, expected["sha256"])
