"""Build only public files for static hosting: python -m scripts.build_frontend."""
import argparse
import os
import shutil
from pathlib import Path

from criclytics_app.paths import PACKAGE_ROOT, PROJECT_ROOT
from criclytics_app.web.security import policy
from criclytics_app.frontend import api_base, runtime_script


def build(output=None, api_origin=None):
    origin = api_base(os.getenv("FRONTEND_API_BASE", "") if api_origin is None else api_origin)
    target = (Path(output) if output else PROJECT_ROOT / "dist").resolve()
    if target == PROJECT_ROOT or PROJECT_ROOT in target.parents and target != PROJECT_ROOT / "dist":
        raise ValueError("Use dist/ or a separate external output directory")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Use a clean output directory; refusing to retain unknown public files")
    target.mkdir(parents=True, exist_ok=True)
    for page in (PACKAGE_ROOT / "templates").glob("*.html"):
        shutil.copy2(page, target / page.name)
    shutil.copytree(PACKAGE_ROOT / "static", target / "static", dirs_exist_ok=True)
    (target / "static/js/runtime-config.js").write_text(runtime_script(origin), encoding="utf-8")
    (target / "_headers").write_text(
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n"
        + "  Content-Security-Policy: " + policy(origin) + "\n"
        + "/static/js/runtime-config.js\n  Cache-Control: no-store\n",
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    parser.add_argument("--api-base", default=None, help="Explicit HTTPS API origin, or empty for same-origin")
    args = parser.parse_args()
    print(build(args.output, args.api_base))
