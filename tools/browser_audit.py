"""Offline Chromium audit: python -m tools.browser_audit.

Requires Playwright and an installed Chrome/Edge browser. Never calls providers.
Third-party visual assets are blocked, so this does not verify their availability.
"""
import json
import threading
from pathlib import Path
from unittest.mock import patch

from werkzeug.serving import make_server

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.web.routes import PAGES


def main():
    from playwright.sync_api import sync_playwright
    from criclytics_app.integrations import rankings
    output = PROJECT_ROOT / "build/audit"
    output.mkdir(parents=True, exist_ok=True)
    cached = PROJECT_ROOT / "data/live/rankings.json"
    ranking_data = json.loads(cached.read_text(encoding="utf-8")) if cached.exists() else rankings.build_hardcoded_rankings()
    app = create_app({"LIVE_FETCH_ENABLED": False, "REDIS_URL": "", "TESTING": True})
    server = make_server("127.0.0.1", 5055, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    cases = []
    queries = {"player-profile.html": "?name=V%20Kohli", "team-profile.html": "?name=India",
               "venue-profile.html": "?name=Lord%27s", "search.html": "?q=Kohli"}
    matches = json.loads((PROJECT_ROOT / "data/processed/completed_matches.json").read_text(encoding="utf-8"))["data"]
    queries["match-detail.html"] = "?id=" + str(matches[0]["id"])
    # Inspect both the fixture page's empty state and a real historical detail.
    with patch("requests.get", side_effect=RuntimeError("Offline browser audit")), \
         patch.object(rankings, "get_current_rankings", return_value=ranking_data), sync_playwright() as pw:
        thread.start()
        browser = pw.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context()
        context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1:5055/") else r.abort())
        for width in [375, 1440]:
            for name in sorted(PAGES):
                page = context.new_page()
                page.set_viewport_size({"width": width, "height": 900})
                errors = []
                failures = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda r: failures.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
                try:
                    page.goto("http://127.0.0.1:5055/" + name + queries.get(name, ""), wait_until="domcontentloaded", timeout=60000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=30000)
                    except Exception:
                        errors.append("Network did not settle within 30s")
                    measure = page.evaluate("""() => ({
                        viewport: innerWidth, document: document.documentElement.scrollWidth,
                        overflow: [...document.querySelectorAll('body *')].filter(e => {
                            const r=e.getBoundingClientRect(); return r.width && (r.right > innerWidth+2 || r.left < -2);
                        }).slice(0,12).map(e => ({tag:e.tagName,id:e.id,classes:String(e.className).slice(0,100)}))
                    })""")
                    item = {"page": name, "width": width, "errors": errors, "http_failures": failures, **measure}
                    if name == "index.html" or measure["document"] > width + 2 or errors:
                        page.screenshot(path=str(output / (name + "-" + str(width) + ".png")), full_page=True)
                except Exception as e:
                    item = {"page": name, "width": width, "errors": errors + [str(e)], "http_failures": failures}
                cases.append(item)
                (output / "browser.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
                print(json.dumps(item), flush=True)
                page.close()
        browser.close()
    server.shutdown()


if __name__ == "__main__":
    main()
