"""Real local-data UI matrix, plus explicit failure, keyboard and long-name cases."""
import json
import argparse
import threading
from pathlib import Path
from werkzeug.serving import make_server
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.web.routes import PAGES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=PROJECT_ROOT/'docs/audit/application-ui-2026-10-28.json')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright
    output = PROJECT_ROOT / 'build/ui-t011'
    output.mkdir(parents=True, exist_ok=True)
    candidate = PROJECT_ROOT / 'build/data-v2-schema-final'
    app = create_app({'PROCESSED_DIR': candidate, 'INITIALIZE_ENGINE': False,
                      'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
    server = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    query = {'player-profile.html': '?name=SC%20Cook', 'team-profile.html': '?name=India',
             'venue-profile.html': '?name=Lord%27s', 'match-detail.html': '?id=1415755',
             'search.html': '?q=Kohli', 'compare.html': '?a=V%20Kohli&b=SPD%20Smith'}
    cases, interactions = [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            for width in (320, 375, 768, 1024, 1440):
                for name in sorted(PAGES):
                    page = browser.new_page(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
                    page.goto(origin + '/' + name + query.get(name, ''), wait_until='networkidle', timeout=60000)
                    result = page.evaluate("""() => ({
                      document:document.documentElement.scrollWidth, viewport:innerWidth,
                      unnamed:[...document.querySelectorAll('input,select,button,summary')].filter(e => e.getClientRects().length &&
                        !(e.labels && e.labels.length) && !e.getAttribute('aria-label') && !e.textContent.trim()).map(e => e.outerHTML.slice(0,120)),
                      loading:[...document.querySelectorAll('[aria-busy=true]')].length,
                      headings:document.querySelectorAll('h1').length
                    })""")
                    result.update(page=name, width=width, errors=errors)
                    cases.append(result)
                    if name in ('index.html', 'team-profile.html') or errors or result['document'] > width + 2:
                        page.screenshot(path=str(output / (name + '-' + str(width) + '.png')), full_page=True)
                    page.close()
                print('Completed width ' + str(width), flush=True)
            # Named and keyboard-operable tabs, denied-image fallback and preserved zero.
            page = browser.new_page(viewport={'width':375,'height':900}, reduced_motion='reduce')
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
            page.goto(origin + '/team-profile.html?name=India', wait_until='networkidle')
            page.locator('[role=tab]').first.focus()
            page.keyboard.press('ArrowRight')
            assert page.locator('[role=tab][aria-selected=true]').inner_text() == 'ODI'
            assert page.locator('#teamCrest').inner_text() == 'I'
            interactions.append({'case':'team denied images and keyboard tabs','passed':True})
            page.goto(origin + '/players.html', wait_until='networkidle')
            page.get_by_label('Player name', exact=True).fill('no-such-player-zzzz')
            page.get_by_role('button',name='Apply filters').click()
            page.wait_for_function("() => document.querySelector('#app').textContent.includes('No records available')")
            interactions.append({'case':'player empty filter','passed':True})
            page.goto(origin + '/match-detail.html', wait_until='networkidle')
            assert 'Select a match' in page.locator('#app').inner_text()
            page.goto(origin + '/player-profile.html?name=Unknown%20Player', wait_until='networkidle')
            assert 'not found' in page.locator('#app').inner_text()
            interactions.append({'case':'missing parameter and unknown entity','passed':True})
            page.route('**/api/players*', lambda route: route.fulfill(status=503, json={'error':'unavailable'}))
            page.goto(origin + '/players.html', wait_until='networkidle')
            assert 'Records are unavailable' in page.locator('#app').inner_text()
            assert not page.locator('#app tbody').count()
            interactions.append({'case':'API503 shows no demo metrics','passed':True})
            page.close()
            browser.close()
    finally:
        server.shutdown()
    report = {'cases':cases,'interactions':interactions,
              'limitations':'Chrome only; external fonts/images denied; uses local schema2.0.1 candidate. Screen-reader speech and hosted latency are not certified.'}
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    failures = [case for case in cases if case['errors'] or case['unnamed'] or case['document'] > case['viewport'] + 2 or case['loading'] or case['headings'] != 1]
    if failures:
        raise AssertionError(json.dumps(failures,indent=2))


if __name__ == '__main__':
    main()
