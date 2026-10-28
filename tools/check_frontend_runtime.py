"""Free local browser checks for request ownership, racing filters and preview configuration."""
import json
import tempfile
import threading
from collections import Counter
from pathlib import Path
from werkzeug.serving import make_server
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.web.routes import PAGES
from tools.check_application_interactions import QuietHandler


def main():
    from playwright.sync_api import sync_playwright
    checks=[]
    with tempfile.TemporaryDirectory() as directory:
        app=create_app({'PROCESSED_DIR':PROJECT_ROOT/'build/data-v2-schema-final','LIVE_DIR':directory,'REDIS_URL':'','LIVE_FETCH_ENABLED':False})
        server=make_server('127.0.0.1',0,app,threaded=True,request_handler=QuietHandler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        origin='http://127.0.0.1:'+str(server.server_port)
        queries={'player-profile.html':'?name=SC%20Cook','team-profile.html':'?name=India','venue-profile.html':"?name=Lord%27s",'match-detail.html':'?id=1415755','match-upcoming.html':'?id=1415755','search.html':'?q=Kohli','compare.html':'?a=V%20Kohli&b=SPD%20Smith'}
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='chrome',headless=True)
                for name in sorted(PAGES):
                    page=browser.new_page(viewport={'width':375,'height':900})
                    errors=[]; requests=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    page.on('request',lambda r:requests.append(r.url) if '/api/' in r.url else None)
                    page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin) else r.abort())
                    page.goto(origin+'/'+name+queries.get(name,''),wait_until='networkidle',timeout=60000)
                    assert not errors,(name,errors)
                    assert all(n==1 for n in Counter(requests).values()),(name,requests)
                    before=len(requests)
                    page.evaluate("() => { const script=document.createElement('script'); script.src='/static/js/application.js'; document.head.append(script); }")
                    page.wait_for_load_state('networkidle')
                    assert len(requests)==before
                    assert not any('/predict/' in url for url in requests)
                    checks.append({'page':name,'requests':len(requests),'duplicate_initialization_requests':0})
                    page.close()
                page=browser.new_page()
                page.goto(origin+'/players.html',wait_until='networkidle')
                # Retain the first request while a later filter response wins.
                held=[]
                def route_players(route):
                    if 'search=older' in route.request.url: held.append(route)
                    else: route.fulfill(json={'players':[{'name':'Newest result','country':'Test','formats':['T20I']}],'total':1})
                page.route('**/api/players?*',route_players)
                page.get_by_label('Player name',exact=True).fill('older')
                page.get_by_role('button',name='Apply filters').click()
                page.wait_for_timeout(100)
                page.get_by_label('Player name',exact=True).fill('newer')
                page.get_by_role('button',name='Apply filters').click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Newest result')")
                assert len(held)==1
                held[0].fulfill(json={'players':[{'name':'Obsolete result','country':'Test','formats':[]}],'total':1})
                page.wait_for_load_state('networkidle')
                assert 'Obsolete result' not in page.locator('#app').inner_text()
                checks.append({'case':'late filter response cannot overwrite newer result','passed':True})
                page.unroute('**/api/players?*')
                calls=[]
                page.route('**/api/players?*',lambda r:(calls.append(r.request.url),r.fulfill(status=503,json={'error':{'code':'unavailable'}})))
                page.get_by_role('button',name='Apply filters').click()
                page.get_by_role('button',name='Try again').wait_for()
                page.get_by_role('button',name='Try again').click()
                page.wait_for_load_state('networkidle')
                assert len(calls)==2
                checks.append({'case':'failure retry is not cached','passed':True})
                page.close()
                # Same page and assets at arbitrary preview origins; explicit API is injected,
                # never derived from the hostname. Browser intercepts only synthetic data.
                html=(PROJECT_ROOT/'criclytics_app/templates/index.html').read_text(encoding='utf-8')
                for preview,base in [('https://preview.example.test','https://api.example.test'),('https://production.example.test','https://api.example.test'),('http://localhost:3000','')]:
                    page=browser.new_page(); calls=[]
                    def preview_route(route):
                        from urllib.parse import urlsplit
                        path=urlsplit(route.request.url).path
                        if path=='/': route.fulfill(body=html,content_type='text/html')
                        elif path=='/static/js/runtime-config.js': route.fulfill(body='window.CRICLYTICS_CONFIG='+json.dumps({'apiBase':base})+';',content_type='application/javascript')
                        elif path.startswith('/static/'):
                            asset=PROJECT_ROOT/'criclytics_app'/path.lstrip('/')
                            route.fulfill(path=str(asset))
                        elif path.startswith('/api/'):
                            calls.append(route.request.url); route.fulfill(json={'data':[],'pagination':{'total':0}})
                        else: route.abort()
                    page.route('**/*',preview_route)
                    page.goto(preview+'/',wait_until='networkidle')
                    assert calls and all(url.startswith((base or preview)+'/api/') for url in calls),(preview,calls)
                    checks.append({'preview':preview,'configured_api':base or 'same-origin','requests':calls})
                    page.close()
                browser.close()
        finally: server.shutdown()
    (PROJECT_ROOT/'docs/audit/frontend-runtime-2026-10-28.json').write_text(json.dumps({'checks':checks,'limitations':'Local Chrome; synthetic preview DNS/API routing; no deployment or production availability claim.'},indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
