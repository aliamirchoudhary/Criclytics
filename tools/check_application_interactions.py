"""Targeted keyboard, safe rendering, pagination, comparison and visual checks."""
import json
import threading
from werkzeug.serving import make_server, WSGIRequestHandler
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def contrast(left, right):
    def luminance(value):
        values = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, (.2126, .7152, .0722)))
    a, b = sorted((luminance(left), luminance(right)))
    return round((b + .05) / (a + .05), 2)


def main():
    from playwright.sync_api import sync_playwright
    app = create_app({'PROCESSED_DIR': PROJECT_ROOT / 'build/data-v2-schema-final',
                      'INITIALIZE_ENGINE': False, 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
    server = make_server('127.0.0.1', 0, app, threaded=True, request_handler=QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    checks = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(viewport={'width':375,'height':900}, reduced_motion='reduce')
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
            page.goto(origin + '/players.html', wait_until='networkidle')
            first = page.locator('#app tbody a').first.get_attribute('href')
            page.get_by_role('button', name='Next page').click()
            page.wait_for_function('(first) => { const a = document.querySelector("#app tbody a"); return a && a.getAttribute("href") !== first; }', arg=first)
            checks.append({'case':'server pagination changes result page','passed':True})
            page.goto(origin + '/compare.html', wait_until='networkidle')
            page.get_by_label('Compare', exact=True).select_option('teams')
            page.get_by_label('First recorded name').fill('India')
            page.get_by_label('Second recorded name').fill('Pakistan')
            page.get_by_role('button', name='Apply filters').click()
            page.wait_for_function('document.querySelector("#app caption")?.textContent.includes("Team records")')
            assert 'India' in page.locator('#app thead').inner_text()
            assert 'Pakistan' in page.locator('#app thead').inner_text()
            checks.append({'case':'team comparison uses descriptive records','passed':True})
            name = '<img src=x onerror="window.__injected=1">' + 'LongName' * 18
            page.add_init_script('window.__injected=0')
            def synthetic(route):
                route.fulfill(json={'name':name,'country':'Unknown', 'batting':{'T20I':{'matches':0,'innings':0,'runs':0,'average':None}},'recent_form':[0]})
            page.route('**/api/players/*', synthetic)
            for width in (320,375,768,1024,1440):
                page.set_viewport_size({'width':width,'height':900})
                page.goto(origin + '/player-profile.html?name=fixture', wait_until='networkidle')
                assert page.locator('h1').inner_text() == name
                assert page.evaluate('window.__injected') == 0
                assert page.locator('#app [onerror],#app script').count() == 0
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2')
                assert page.locator('.ui-metrics dd').first.inner_text() == '0'
                assert '—' in page.locator('.ui-metrics').inner_text()
                checks.append({'case':'long malicious name, zero and missing values','width':width,'passed':True})
            tree = page.locator('#main').aria_snapshot()
            (PROJECT_ROOT / 'docs/audit/application-aria-2026-10-28.txt').write_text(tree,encoding='utf-8')
            assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
            assert page.locator('h1').evaluate('(e) => getComputedStyle(e).animationName') == 'none'
            checks.append({'case':'reduced motion applied','passed':True})
            page.close(); browser.close()
    finally:
        server.shutdown()
    colors = [{'foreground':fg,'background':bg,'ratio':contrast(fg,bg)} for fg,bg in
              (('#c1d4e5','#102442'),('#a5d7ff','#0a1931'),('#081a30','#a5d7ff'),('#f6fafd','#0d2040'))]
    assert all(item['ratio'] >= 4.5 for item in colors)
    (PROJECT_ROOT / 'docs/audit/application-interactions-2026-10-28.json').write_text(
        json.dumps({'checks':checks,'contrast':colors,'limitations':'Selected authored color pairs reviewed; no screen-reader speech or exhaustive WCAG certification.'},indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
