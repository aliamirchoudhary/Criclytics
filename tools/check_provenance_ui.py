"""Offline source-label smoke on the three ranking entry pages."""
import json
import threading
from werkzeug.serving import make_server
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def main():
    from playwright.sync_api import sync_playwright
    app = create_app({'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
    server = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    evidence = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            for filename in ('index.html', 'rankings.html', 'team-profile.html?name=Pakistan'):
                page = browser.new_page(viewport={'width': 375, 'height': 900})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def handler(route):
                    url = route.request.url
                    if not url.startswith(origin):
                        route.abort()
                    elif '/api/' in url and '/api/icc-rankings?' not in url:
                        route.fulfill(json={'data': []})
                    else:
                        route.continue_()
                page.route('**/*', handler)
                page.goto(origin + '/' + filename, wait_until='networkidle')
                page.evaluate("apiFetch('/api/icc-rankings?category=teams&format=ODI')")
                label = page.locator('#source-notice-rankings').inner_text()
                assert '2026-04' in label and 'Fallback snapshot' in label and 'Stale' in label, label
                evidence.append({'page': filename, 'label': label, 'errors_with_stubbed_other_data': errors})
                page.close()
            browser.close()
    finally:
        server.shutdown()
    (PROJECT_ROOT / 'docs/audit/provenance-ui-2026-10-28.json').write_text(
        json.dumps({'pages': evidence, 'limitations': 'Source-label acceptance only; other endpoints stubbed, external assets blocked.'}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
