"""Offline adversarial DOM/CSP smoke. Requires Playwright and Chrome."""
import json
import threading
from pathlib import Path

from werkzeug.serving import make_server

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def main():
    from playwright.sync_api import sync_playwright
    app = create_app({"TESTING": True, "LIVE_FETCH_ENABLED": False, "REDIS_URL": "",
                      "INITIALIZE_ENGINE": False})
    server = make_server("127.0.0.1", 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = "http://127.0.0.1:" + str(server.server_port)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page()
            page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin)
                       else route.abort())
            page.goto(origin + "/about.html", wait_until="networkidle")
            result = page.evaluate("""() => {
                window.__injected = 0;
                const node = document.createElement('div'); document.body.append(node);
                node.innerHTML = '<img src=x onerror="window.__injected=1"><script>window.__injected=2</script><a href="javascript:window.__injected=3">bad</a>';
                const table = document.createElement('table');
                const body = document.createElement('tbody'); table.append(body);
                body.innerHTML = '<tr><td>safe</td></tr>';
                const flag = flagHtml('<img src=x onerror=window.__injected=4>');
                node.insertAdjacentHTML('beforeend', flag);
                return {handlers:node.querySelectorAll('[onerror],[onclick],script').length,
                  unsafeHref:node.querySelector('a').getAttribute('href'),
                  rows:body.rows.length,cell:body.textContent,
                  imageUrl:safeImageUrl('https://evil.example/track'),
                  credentialUrl:safeImageUrl('https://user:pass@h.cricapi.com/image.png'),
                  escaped:esc(`'"<>&`)};
            }""")
            page.wait_for_timeout(100)
            result["executed"] = page.evaluate("window.__injected")
            assert result["handlers"] == 0, result
            assert not result["unsafeHref"], result
            assert result["rows"] == 1 and result["cell"] == "safe", result
            assert not result["imageUrl"] and not result["credentialUrl"], result
            assert result["executed"] == 0, result
            assert "&#39;" in result["escaped"], result
            cases = []
            for filename, expression in [
                ("search.html", "buildPlayerCard({name:bad,country:bad,runs:bad,photo:'javascript:alert(1)'})"),
                ("compare.html", "flagHtml(bad)"),
                ("player-profile.html", "flagHtml(bad)"),
            ]:
                page.goto(origin + "/" + filename, wait_until="domcontentloaded")
                page.wait_for_function("typeof flagHtml === 'function'")
                code = """() => {
                    const bad = `<img src=x onerror='window.__injected=9'>O'Neil`;
                    window.__injected=0;
                    const box=document.createElement('div');document.body.append(box);
                    box.innerHTML=EXPRESSION;
                    return {page:location.pathname,handlers:box.querySelectorAll('[onerror],script').length};
                }""".replace("EXPRESSION", expression)
                case = page.evaluate(code)
                page.wait_for_timeout(50)
                case["executed"] = page.evaluate("window.__injected")
                assert case["handlers"] == 0 and case["executed"] == 0, case
                cases.append(case)
            result["page_cases"] = cases
            # CSP enforcement does not rely on report-only scripts.
            assert "object-src 'none'" in page.request.get(origin + "/").headers["content-security-policy"]
            browser.close()
        output = PROJECT_ROOT / "docs/audit/dom-security-2026-10-28.json"
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
