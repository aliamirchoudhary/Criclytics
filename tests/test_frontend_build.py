"""Exercise the deployment build in a fresh checkout without site packages."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent


class FrontendBuildTests(unittest.TestCase):
    def test_clean_cli_build_needs_no_backend_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            for name in ("criclytics_app", "scripts"):
                shutil.copytree(ROOT / name, checkout / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run(
                [sys.executable, "-S", "-m", "scripts.build_frontend"],
                cwd=checkout, env=env, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = checkout / "dist"
            self.assertEqual(len(list(output.glob("*.html"))), 19)
            self.assertTrue((output/'workspace.html').is_file())
            self.assertTrue((output/'scouting.html').is_file())
            self.assertTrue((output / "static/js/cricklytics.js").is_file())
            self.assertTrue((output / "static/css/styles.css").is_file())
            self.assertFalse(list(output.rglob("*.py")))
            self.assertFalse(list(output.rglob(".env")))
