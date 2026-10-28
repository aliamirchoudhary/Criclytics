"""Offline browser checks for the withdrawn prediction surfaces."""
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
    cases = [('compare.html', '.prob-compare-section', None),
             ('match-detail.html?id=test-live', '#win-prob-card', None),
             ('match-upcoming.html', '.prediction-unavailable', None),
             ('player-profile.html?name=SC%20Cook', '#panel-probability',
              "renderPlayerProbabilityTab('SC Cook','Test')"),
             ('team-profile.html?name=Pakistan', '#panel-probability', None),
             ('venue-profile.html?name=Lords', '#panel-insights', None)]
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            for width in (375, 1440):
                for filename, selector, render in cases:
                    page = browser.new_page(viewport={'width': width, 'height': 900})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    def handler(route):
                        url = route.request.url
                        if not url.startswith(origin):
                            route.abort()
                        elif '/api/matches/test-live' in url:
                            route.fulfill(json={'data': {'id': 'test-live', 'teams': ['India', 'Pakistan'],
                                'matchStarted': True, 'matchEnded': False, 'matchType': 'ODI'}})
                        elif '/api/' in url and '/api/predict/' not in url:
                            route.fulfill(status=404, json={'error': 'unavailable'})
                        else:
                            route.continue_()
                    page.route('**/*', handler)
                    page.goto(origin + '/' + filename, wait_until='networkidle')
                    if render:
                        page.evaluate(render)
                    text = page.locator(selector).first.text_content()
                    assert 'unavailable' in text.lower() and '%' not in text, text
                    response = page.request.get(origin + '/api/predict/player/SC%20Cook?format=Test&metric=100')
                    assert response.json()['probability'] is None
                    evidence.append({'page': filename, 'width': width, 'message': text.strip(),
                                     'errors_with_other_data_unavailable': errors})
                    page.close()
            browser.close()
    finally:
        server.shutdown()
    (PROJECT_ROOT / 'docs/audit/prediction-ui-2026-10-28.json').write_text(
        json.dumps({'cases': evidence, 'limitations': 'Prediction containment only; other APIs forced unavailable and external assets blocked.'}, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
