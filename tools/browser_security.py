"""Offline adversarial DOM/CSP smoke. Requires Playwright and Chrome."""
import argparse
import json
import threading

from werkzeug.serving import make_server

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def main():
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    app = create_app({"TESTING": True, "LIVE_FETCH_ENABLED": False, "REDIS_URL": "",
                      "INITIALIZE_ENGINE": False})
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel=None if args.channel == 'chromium' else args.channel, headless=True)
            page = browser.new_page()
            page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin)
                       else route.abort())
            page.goto(origin + "/about.html", wait_until="networkidle")
            result = page.evaluate("""() => {
                window.__injected = 0;
                const bad = `<img src=x onerror='window.__injected=9'>O'Neil`;
                const box = CriclyticsDOM.node('div', bad);
                box.append(CriclyticsMedia.flag(bad), CriclyticsMedia.portrait({name:bad},false));
                document.body.append(box);
                const script = document.createElement('script');
                script.textContent = 'window.__injected=1'; document.body.append(script);
                return {handlers:box.querySelectorAll('[onerror],script').length,
                        textPreserved:box.textContent.includes(bad),
                        foreignImages:[...box.querySelectorAll('img')].some(i=>i.src.startsWith('https://'))};
            }""")
            page.wait_for_timeout(100)
            result['executed'] = page.evaluate('window.__injected')
            assert result['handlers'] == 0 and result['textPreserved'], result
            assert not result['foreignImages'] and result['executed'] == 0, result
            # CSP enforcement does not rely on report-only scripts.
            assert "object-src 'none'" in page.request.get(origin + "/").headers["content-security-policy"]
            browser.close()
        output = PROJECT_ROOT / "build/audit-fixes-dom-security.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
