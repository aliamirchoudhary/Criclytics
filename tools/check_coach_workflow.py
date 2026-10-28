"""Local coach task simulation, not actual coach validation or hosted storage."""
import json
from pathlib import Path
import tempfile
import threading
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT


def main():
    app=create_app({'PROCESSED_DIR':PROJECT_ROOT/'build/data-v3-manifest-final',
                    'IDENTITY_REGISTRY':PROJECT_ROOT/'build/identities-v1-final.json',
                    'IDENTITY_PLAYER_STORE':PROJECT_ROOT/'build/player-ids-v1-final',
                    'SCOUTING_SAMPLE':PROJECT_ROOT/'build/scouting-delivery-v1.json',
                    'LIVE_DIR':PROJECT_ROOT/'build/t029-live','REDIS_URL':'','LIVE_FETCH_ENABLED':False})
    server=make_server('127.0.0.1',0,app,threaded=True);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:'+str(server.server_port);cases=[]
    try:
        with tempfile.TemporaryDirectory() as directory,sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            for width in (375,1440):
                page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce');calls=[];errors=[]
                page.on('request',lambda req:calls.append({'url':req.url,'body':req.post_data}))
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(base+'/scouting.html?player=V%20Kohli')
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Report:')")
                page.get_by_label('Private tactical notes',exact=True).fill('PRIVATE-NOTE-SENTINEL <img src=x onerror=alert(1)>')
                page.get_by_label('Private roster',exact=True).fill('PRIVATE-ROSTER-SENTINEL')
                page.get_by_label('What-if assumptions',exact=True).fill('PRIVATE-ASSUMPTION-SENTINEL: select a venue; no causal claim')
                page.get_by_label('Opponent source name (optional)',exact=True).fill('Pakistan')
                assert 'Selections changed' in page.locator('#app').inner_text()
                page.get_by_role('button',name='Prepare evidence',exact=True).click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Report:')")
                assert page.get_by_label('Private tactical notes',exact=True).input_value().startswith('PRIVATE-NOTE')
                with page.expect_download() as download:page.get_by_role('button',name='Export private plan',exact=True).click()
                plan=Path(directory)/('plan-'+str(width)+'.json');download.value.save_as(plan)
                payload=json.loads(plan.read_text(encoding='utf-8'));assert payload['evidence']['report_id'];assert 'PRIVATE-NOTE' in payload['notes']
                with page.expect_download() as download:page.get_by_role('button',name='Export public evidence',exact=True).click()
                public=Path(directory)/('public-'+str(width)+'.json');download.value.save_as(public)
                assert 'PRIVATE-' not in public.read_text(encoding='utf-8')
                assert not any('PRIVATE-' in str(call) for call in calls),calls
                assert page.evaluate('localStorage.length')==0
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.reload();page.wait_for_function("() => document.querySelector('#app').textContent.includes('Report:')")
                assert page.get_by_label('Private tactical notes',exact=True).input_value()==''
                page.get_by_label('Import private plan from a local file',exact=True).set_input_files(plan)
                page.get_by_text('Plan restored in this page. Imported evidence is unverified until refreshed. Nothing uploaded.',exact=True).wait_for()
                assert page.get_by_label('Private tactical notes',exact=True).input_value()==payload['notes']
                bad=Path(directory)/'bad.json';bad.write_text('{"notes":"overwrite"}')
                page.get_by_label('Import private plan from a local file',exact=True).set_input_files(bad)
                page.get_by_text('Invalid or oversized plan. Existing private fields were preserved.',exact=True).wait_for()
                assert page.get_by_label('Private tactical notes',exact=True).input_value()==payload['notes']
                other=browser.new_page();other.goto(base+'/scouting.html')
                other.get_by_label('Private tactical notes',exact=True).wait_for();assert other.get_by_label('Private tactical notes',exact=True).input_value()=='';other.close()
                assert not errors,errors
                cases.append({'width':width,'prepare_and_filter':True,'private_export_import':True,'public_export_excludes_notes':True,
                              'private_not_transmitted':True,'refresh_loss_explicit':True,'separate_tab_isolation':True,'invalid_import_preserves_fields':True,'page_errors':errors})
                page.close()
            browser.close()
    finally:server.shutdown();thread.join(timeout=5);server.server_close()
    result={'browser':cases,'actual_coach_feedback':None,'limitations':'Agent task simulation with actual local ID candidate and limited historical delivery sample; real coach feedback/pilot pending. No server private persistence/accounts are claimed.'}
    (PROJECT_ROOT/'docs/audit/coach-workflow-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main()
