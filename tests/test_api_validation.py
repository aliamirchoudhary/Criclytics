import tempfile
import unittest

from criclytics_app import create_app


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "INITIALIZE_ENGINE": False,
                               "LIVE_FETCH_ENABLED": False, "REDIS_URL": "",
                               "PROCESSED_DIR": self.temp.name, "LIVE_DIR": self.temp.name})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_numbers_are_rejected_before_missing_data(self):
        for endpoint in ("players", "search", "rankings", "predict/leaderboard"):
            for value in ("nope", "-1", "0", "501", "99999999999", "1.5"):
                with self.subTest(endpoint=endpoint, value=value):
                    result = self.client.get("/api/" + endpoint + "?limit=" + value)
                    self.assertEqual(result.status_code, 400)
                    self.assertIn("request_id", result.json)

    def test_types_and_formats(self):
        for payload in ([], "text", 12, None, {}, {"team_a": [], "team_b": "India"},
                        {"team_a": "India", "team_b": "Pakistan", "format": "invalid"},
                        {"team_a": "India", "team_b": "Pakistan", "format": []}):
            result = self.client.post("/api/predict/team_match", json=payload)
            self.assertIn(result.status_code, (400, 415))
        self.assertEqual(self.client.post("/api/predict/team_match", data="hello").status_code, 415)
        self.assertEqual(self.client.get("/api/players?format=garbage").status_code, 400)
        self.assertEqual(self.client.get("/api/search?q=" + "x" * 201).status_code, 400)
        self.assertEqual(self.client.get("/api/players?limit=1&limit=2").status_code, 400)

    def test_missing_artifact_unknown_route_and_size(self):
        self.assertEqual(self.client.get("/api/players").status_code, 503)
        self.assertEqual(self.client.get("/api/not-a-route").status_code, 404)
        result = self.client.post("/api/predict/team_match", data="x" * 65537,
                                  content_type="application/json")
        self.assertEqual(result.status_code, 413)

    def test_server_error_is_redacted(self):
        @self.app.get("/api/test-failure")
        def fail():
            raise RuntimeError("private-token-must-never-leak")
        response = self.client.get("/api/test-failure")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private-token", response.get_data(as_text=True))
        self.assertIn("X-Request-ID", response.headers)
