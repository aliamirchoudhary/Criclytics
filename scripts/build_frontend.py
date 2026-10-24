"""Build only public files for static hosting: python -m scripts.build_frontend."""
import argparse
import shutil
from pathlib import Path

from criclytics_app.paths import PACKAGE_ROOT, PROJECT_ROOT


def build(output=None):
    target = (Path(output) if output else PROJECT_ROOT / "dist").resolve()
    if target == PROJECT_ROOT or PROJECT_ROOT in target.parents and target != PROJECT_ROOT / "dist":
        raise ValueError("Use dist/ or a separate external output directory")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Use a clean output directory; refusing to retain unknown public files")
    target.mkdir(parents=True, exist_ok=True)
    for page in (PACKAGE_ROOT / "templates").glob("*.html"):
        shutil.copy2(page, target / page.name)
    shutil.copytree(PACKAGE_ROOT / "static", target / "static", dirs_exist_ok=True)
    (target / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    print(build(parser.parse_args().output))
