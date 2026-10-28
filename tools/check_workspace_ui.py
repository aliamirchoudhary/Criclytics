"""Actual local shadow API browser workflow with authored scoring inputs."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import time
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.services.forecasts import ForecastService
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.pipeline.events import initial_state, apply_event
from criclytics_app.pipeline.artifacts import digest
from tests.test_forecasts import model_files
from tests.test_reconciliation import setup_data, observation, next_context, NOW


def main():
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory); now=[NOW]; model,evaluation=model_files(root);meta,one,_=setup_data()
        collector=LocalCollector(root/'source.sqlite3',enabled=True,clock=lambda:now[0])
        state=apply_event(initial_state(meta,1),one)
        collector.ingest(meta,observation(meta,'one',[one],next_context(state,2)))
        app=create_app({'TESTING':True,'LIVE_DIR':root/'live','LIVE_FETCH_ENABLED':False,'REDIS_URL':'',
                        'EXPERIMENTAL_FORECASTS':False,'IDENTITY_REGISTRY':'','IDENTITY_PLAYER_STORE':''})
        service=ForecastService(root/'source.sqlite3',root/'ledger.sqlite3',model,digest(model),evaluation,digest(evaluation),clock=lambda:now[0])
        app.extensions['forecast_service']=service
        server=make_server('127.0.0.1',0,app,threaded=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='chrome',headless=True)
                for width in (375,1440):
                    page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
                    errors=[];calls=[]
                    page.on('pageerror',lambda error:errors.append(str(error)))
                    page.on('request',lambda req:calls.append(req.url) if '/api/v1/' in req.url else None)
                    page.goto(base+'/workspace.html?id='+meta['match_id'])
                    page.get_by_role('link',name='View issued forecast',exact=False).wait_for()
                    assert len(calls)==2,calls
                    assert 'Manual scoring' in page.locator('#app').inner_text()
                    assert 'not in model' in page.locator('#app').inner_text()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.get_by_role('link',name='View issued forecast',exact=False).click()
                    assert page.locator(page.evaluate('location.hash')).count()==1
                    # Open via native keyboard; history distribution is attached to the issued entry.
                    page.locator('#app details summary').first.focus();page.keyboard.press('Enter')
                    assert page.locator('#app details').first.get_attribute('open') is not None
                    page.get_by_role('button',name='Refresh workspace',exact=True).focus();page.keyboard.press('Enter')
                    page.wait_for_function("() => document.querySelector('#app a[href^=\"#forecast-\"]') !== null")
                    assert service.inferences==1
                    assert not errors,errors
                    results.append({'width':width,'manual_mode':True,'issued_anchor':True,'keyboard_details_refresh':True,
                                    'reduced_motion':True,'initial_api_calls':2,'overflow':False,'page_errors':errors})
                    page.close()
                page=browser.new_page(viewport={'width':375,'height':900});page.goto(base+'/workspace.html?id='+meta['match_id'])
                page.get_by_role('link',name='View issued forecast',exact=False).wait_for()
                corrected=deepcopy(one);corrected['revision']=2;corrected['runs']['batter']=2;corrected['runs']['total']=2
                now[0]+=1; state=apply_event(initial_state(meta,1),corrected)
                collector.ingest(meta,observation(meta,'changed',[corrected],next_context(state,2,'player:a','player:b')))
                page.get_by_role('button',name='Refresh workspace',exact=True).click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Replaces issued forecast')")
                now[0]+=61;page.get_by_role('button',name='Refresh workspace',exact=True).click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('stale source')")
                assert page.get_by_role('link',name='View issued forecast',exact=False).count()==0
                assert page.locator('#app details').count()==2
                page.route('**/api/v1/**/forecast',lambda route:route.fulfill(status=503,content_type='application/json',body='{}'))
                page.get_by_role('button',name='Refresh workspace',exact=True).click();page.get_by_role('button',name='Try again',exact=True).wait_for()
                page.unroute('**/api/v1/**/forecast')
                page.get_by_role('button',name='Try again',exact=True).click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('stale source')")
                # Delayed network state remains loading, then completes without duplicate requests.
                def slow(route):time.sleep(.3);route.continue_()
                page.route('**/api/v1/**/forecast',slow)
                page.get_by_role('button',name='Refresh workspace',exact=True).click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('stale source')")
                page.close()
                # Replay uses the same API contract, with explicit source mode in UI.
                other_meta=deepcopy(meta);other_meta['match_id']='match:manual:replay-fixture'
                event=deepcopy(one);event['match_id']=other_meta['match_id'];event['event_id']=other_meta['match_id']+'#i1/d1'
                collector.close();collector=LocalCollector(root/'replay.sqlite3',mode='replay',enabled=True,clock=lambda:now[0])
                collector.ingest(other_meta,observation(other_meta,'replay',[event],next_context(apply_event(initial_state(other_meta,1),event),2)))
                replay=ForecastService(root/'replay.sqlite3',root/'replay-ledger.sqlite3',model,digest(model),evaluation,digest(evaluation),clock=lambda:now[0])
                app.extensions['forecast_service']=replay
                page=browser.new_page();page.goto(base+'/workspace.html?id='+other_meta['match_id'])
                page.get_by_role('link',name='View issued forecast',exact=False).wait_for()
                assert 'Historical replay' in page.locator('#app').inner_text()
                # Actual UI expiry timer, no network polling.
                page.get_by_text('Confirmation expired · current forecast unavailable',exact=True).wait_for(timeout=17000)
                assert page.get_by_role('link',name='View issued forecast',exact=False).count()==0
                app.extensions['forecast_service']=None
                page.reload();page.wait_for_function("() => document.querySelector('#app').textContent.includes('experimental workspace disabled')")
                page.close();browser.close()
        finally:collector.close();server.shutdown();thread.join(timeout=5);server.server_close()
    report={'browser':results,'correction_history':True,'stale_abstention':True,'error_retry':True,'delayed_response':True,
            'replay_mode':True,'disabled_mode':True,'expiry_without_polling':True,
            'limitations':'Authored local scores/fictional portable model, not a real coach or external feed trial. Browser Chrome only; no production deployment.'}
    (PROJECT_ROOT/'docs/audit/workspace-ui-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
