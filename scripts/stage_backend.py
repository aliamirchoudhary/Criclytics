"""Create an allowlisted HF upload artifact; never upload the checkout itself."""
import argparse
import shutil
from pathlib import Path

from criclytics_app.paths import PROJECT_ROOT


def stage(output=None):
    output = (Path(output) if output else PROJECT_ROOT / "build/backend").resolve()
    if output == PROJECT_ROOT or PROJECT_ROOT in output.parents and output != PROJECT_ROOT / "build/backend":
        raise ValueError("Use build/backend or a separate external output directory")
    # This is a new build directory, not a source/data directory.
    if output.exists():
        raise FileExistsError("build/backend already exists; use a clean checkout to stage a release")
    output.mkdir(parents=True)
    for name in ["app.py", "wsgi.py", "requirements.txt", "Dockerfile", ".dockerignore", "README.md"]:
        shutil.copy2(PROJECT_ROOT / name, output / name)
    shutil.copytree(PROJECT_ROOT / "criclytics_app", output / "criclytics_app",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(PROJECT_ROOT / "data/static", output / "data/static")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    print(stage(parser.parse_args().output))
