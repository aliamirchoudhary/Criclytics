"""Offline Chromium audit: python -m tools.browser_audit.

Requires Playwright and an installed Chrome/Edge browser. Never calls providers.
Third-party visual assets are blocked, so this does not verify their availability.
"""
import argparse
import contextlib
import io
import json
import tempfile
from urllib.parse import urlencode
import threading
from pathlib import Path
from unittest.mock import patch

from werkzeug.serving import make_server

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.web.routes import PAGES


def main():
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', default='chrome', help='chrome or chromium (installed Playwright browser)')
    parser.add_argument('--output', type=Path, default=PROJECT_ROOT / 'build/audit-fixes-browser')
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    # Always use fictional CC0 fixtures; never depend on ignored developer data.
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        root = Path(directory)
        pack = json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))
        folders = {'Test':'tests_male_json', 'ODI':'odis_male_json', 'T20':'t20s_male_json'}
        for fixture in pack['fixtures']:
            path = root/'raw'/folders[fixture['match']['info']['match_type']]/(fixture['id']+'.json')
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(fixture['match']),encoding='utf-8')
        from criclytics_app.pipeline.rebuild import rebuild
        with contextlib.redirect_stdout(io.StringIO()):
            rebuild(root/'raw',root/'processed')
        players = json.loads((root/'processed/players_index.json').read_text(encoding='utf-8'))
        teams = json.loads((root/'processed/team_format_stats.json').read_text(encoding='utf-8'))
        venues = json.loads((root/'processed/venue_stats.json').read_text(encoding='utf-8'))
        matches = json.loads((root/'processed/completed_matches.json').read_text(encoding='utf-8'))['data']
        query = lambda **kw: '?' + urlencode(kw)
        queries = {'player-profile.html':query(name=next(iter(players))),
                   'team-profile.html':query(name=next(iter(teams))),
                   'venue-profile.html':query(name=next(iter(venues))),
                   'search.html':query(q=next(iter(players))),
                   'match-detail.html':query(id=matches[0]['id'])}
        app = create_app({'PROCESSED_DIR':str(root/'processed'),'LIVE_DIR':str(root/'live'),
                          'DATASET_STORE':'','IDENTITY_REGISTRY':'','IDENTITY_PLAYER_STORE':'',
                          'SCENARIO_MODEL':'','EXPERIMENTAL_FORECASTS':False,
                          'LIVE_FETCH_ENABLED':False,'REDIS_URL':'','TESTING':True})
        server = make_server('127.0.0.1',0,app,threaded=True)
        base = 'http://127.0.0.1:' + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        stack.enter_context(patch('requests.get',side_effect=AssertionError('Offline browser audit')))
        pw = stack.enter_context(sync_playwright())
        cases = []
        thread.start()
        stack.callback(server.server_close)
        stack.callback(server.shutdown)
        browser = pw.chromium.launch(channel=None if args.channel == "chromium" else args.channel, headless=True)
        stack.callback(browser.close)
        context = browser.new_context()
        context.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base + "/") else r.abort())
        for width in [375, 1440]:
            for name in sorted(PAGES):
                page = context.new_page()
                page.set_viewport_size({"width": width, "height": 900})
                errors = []
                failures = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda r: failures.append({"url": r.url, "status": r.status}) if r.status >= 400 else None)
                try:
                    page.goto(base + "/" + name + queries.get(name, ""), wait_until="domcontentloaded", timeout=60000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=30000)
                    except Exception:
                        errors.append("Network did not settle within 30s")
                    # Exercise shared navigation and search instead of only checking links.
                    navigation = page.locator('nav[aria-label="Primary"]')
                    summary = page.locator('.ui-navigation > summary')
                    if summary.is_visible():
                        summary.click()
                        if not navigation.is_visible():
                            errors.append('Primary navigation failed to open')
                        summary.click()
                    elif not navigation.is_visible():
                        errors.append('Desktop primary navigation is missing')
                    if name == 'index.html':
                        page.locator('#global-search').fill(next(iter(players)))
                        page.locator('form[role="search"] button').click()
                        page.wait_for_url('**/search.html?**')
                        page.wait_for_load_state('networkidle')
                        if not page.locator('#app').inner_text().strip():
                            errors.append('Search navigation rendered no content')
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
        failed = [item for item in cases if item['errors'] or item['http_failures']
                  or item.get('document',0) > item['width'] + 2]
        if failed:
            raise SystemExit(f'Browser regression: {len(failed)} failed cases; see browser.json')


if __name__ == "__main__":
    main()
