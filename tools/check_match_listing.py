"""Offline full-data payload timings and real-browser pagination smoke."""
import json
import threading
import time
from unittest.mock import patch

from werkzeug.serving import make_server
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def main():
    from playwright.sync_api import sync_playwright
    app = create_app({'TESTING': True, 'INITIALIZE_ENGINE': False,
                      'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
    measurements = []
    with app.test_client() as client:
        for label in ('cold_process', 'warm_process'):
            start = time.perf_counter()
            response = client.get('/api/matches')
            measurements.append({'mode': label, 'bytes': len(response.data),
                                 'milliseconds': round((time.perf_counter() - start) * 1000, 2),
                                 'total': response.json['pagination']['total']})
            assert response.status_code == 200 and len(response.data) < 250 * 1024
        mid = response.json['data'][0]['id']
        start = time.perf_counter()
        detail = client.get('/api/matches/' + mid)
        measurements.append({'mode': 'detail', 'bytes': len(detail.data),
                             'milliseconds': round((time.perf_counter() - start) * 1000, 2)})
        assert detail.status_code == 200
    fixtures = [dict(id=str(i), teams=['Pakistan', 'India'], date='2026-01-01',
                     matchType='T20', venue='Ground', name='Pakistan vs India') for i in range(27)]
    server = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    browsers = []
    try:
        with patch('criclytics_app.api.routes.completed_summaries', return_value=fixtures), \
             patch('criclytics_app.api.routes.fetch_cricapi', return_value=None), \
             patch('criclytics_app.api.routes.load_live', return_value=None), sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            for width in (375, 1440):
                page = browser.new_page(viewport={'width': width, 'height': 900})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def route_request(route):
                    url = route.request.url
                    if not url.startswith(origin):
                        route.abort()
                    elif '/api/' in url and '/api/matches?' not in url:
                        route.fulfill(json={'data': []})
                    else:
                        route.continue_()
                page.route('**/*', route_request)
                page.goto(origin + '/matches.html', wait_until='networkidle')
                page.locator('.status-tab[data-status="completed"]').click()
                page.wait_for_function("document.querySelectorAll('#group-completed a.match-row-card').length === 10")
                first = page.locator('#group-completed a.match-row-card').first.get_attribute('href')
                page.locator('#group-completed .page-btn[data-page="2"]').first.click()
                page.wait_for_function("_ps['group-completed'] === 2")
                second = page.locator('#group-completed a.match-row-card').first.get_attribute('href')
                assert first != second
                page.locator('.filter-chip[data-format="odi"]').click()
                page.wait_for_function("_ms['group-completed'].serverTotal === 0")
                assert not errors, errors
                browsers.append({'width': width, 'first': first, 'second': second,
                                 'filter_empty': True, 'page_errors': errors})
                page.close()
            browser.close()
    finally:
        server.shutdown()
    (PROJECT_ROOT / 'docs/audit/match-listing-2026-10-28.json').write_text(
        json.dumps({'measurements': measurements, 'browser': browsers,
                    'limitations': 'Cold process is not an OS disk-cache flush. Browser uses synthetic fixtures; external resources blocked.'}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
