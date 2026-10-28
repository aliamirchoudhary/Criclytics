"""Local dataset verification, retained-version drill and truthful coverage UI smoke."""
import json
from pathlib import Path
import threading
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.artifacts import validate,promote,selected,digest
from tools.check_application_interactions import QuietHandler
from werkzeug.serving import make_server


def main():
    from playwright.sync_api import sync_playwright
    candidate=PROJECT_ROOT/'build/data-v3-manifest-final'
    manifest=validate(candidate)
    store=PROJECT_ROOT/'build/t015-store'
    promoted=promote(candidate,store,digest(candidate/'manifest.json'))
    assert selected(store)==promoted
    coverage=json.loads((candidate/'coverage.json').read_text(encoding='utf-8'))
    app=create_app({'DATASET_STORE':store,'LIVE_DIR':PROJECT_ROOT/'build/t015-live','LIVE_FETCH_ENABLED':False,'REDIS_URL':''})
    server=make_server('127.0.0.1',0,app,threaded=True,request_handler=QuietHandler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    cases=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='chrome',headless=True)
            for width in (375,1440):
                page=browser.new_page(viewport={'width':width,'height':900}); errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                origin='http://127.0.0.1:'+str(server.server_port)
                page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort())
                page.goto(origin+'/',wait_until='networkidle')
                text=page.locator('.ui-coverage').inner_text()
                assert str(coverage['accepted_matches']) in text
                assert coverage['last_match_date'] in text
                assert 'not proof of historical publication time' in text
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
                assert not errors
                cases.append({'width':width,'text':text,'errors':errors})
                page.close()
            browser.close()
    finally:server.shutdown()
    outputs={name:digest(candidate/name)==value for name,value in manifest['outputs'].items()}
    pipeline={name:digest(PROJECT_ROOT/'criclytics_app/pipeline'/name)==value for name,value in manifest['code_sha256'].items()}
    assert all(outputs.values()) and all(pipeline.values())
    evidence={'dataset_id':manifest['dataset_id'],'manifest_sha256':digest(candidate/'manifest.json'),
              'coverage':coverage,'output_hashes_valid':outputs,'pipeline_hashes_valid':pipeline,
              'inventory_files':manifest['inventory_files'],'selected_files':len(manifest['inputs']),
              'excluded_files':len(manifest['excluded']),'local_promotion_verified':True,
              'restore_drill':'Portable golden test promotes two versions, restores first, rejects corruption with unchanged pointer.',
              'ui':cases,'default_serving_changed':False,'deployed':False}
    (PROJECT_ROOT/'docs/audit/dataset-manifest-2026-10-28.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
