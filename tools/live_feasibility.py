"""Synthetic replay timing experiment; no provider, network, credentials or wall-clock waiting."""
import json
from criclytics_app.paths import PROJECT_ROOT


def simulate(interval,delay=0):
    # Fictional deliveries and a correction with exact known virtual availability.
    events=[{'id':i,'revision':1,'occurred':i*40,'available':i*40+delay} for i in range(1,37)]
    events.append({'id':12,'revision':2,'occurred':480,'available':600+delay})
    seen={};latencies=[];calls=0;on_time=set();corrections=0
    for tick in range(0,1600,interval):
        calls+=1
        for event in events:
            key=(event['id'],event['revision'])
            if event['available']<=tick and key not in seen:
                seen[key]=tick
                if event['revision']==1:
                    latencies.append(tick-event['occurred'])
                    if tick<event['occurred']+40:on_time.add(event['id'])
                else:corrections+=1
    return {'virtual_poll_seconds':interval,'assumed_source_delay_seconds':delay,'synthetic_requests':calls,
            'initial_deliveries_seen':sum(revision==1 for _,revision in seen),
            'missed_initial_deliveries':36-sum(revision==1 for _,revision in seen),
            'delivery_states_received_before_following_delivery':len(on_time),
            'opportunities_too_late':36-len(on_time),'corrections_seen':corrections,
            'correction_observation_delay_seconds':seen.get((12,2),600)-600,
            'lag_seconds':{'min':min(latencies),'max':max(latencies),'mean':sum(latencies)/len(latencies)}}


def main():
    from playwright.sync_api import sync_playwright
    browser_check={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page();page.set_content('<main><p id="score">0</p></main>')
        session=page.context.new_cdp_session(page);session.send('Performance.enable')
        values={row['name']:row['value'] for row in session.send('Performance.getMetrics')['metrics']}
        page.evaluate("document.querySelector('#score').id='revised-score'")
        browser_check={'synthetic_selector_break_observed':page.locator('#score').count()==0,
                       'renderer_js_heap_used_bytes':int(values.get('JSHeapUsedSize',0)),
                       'total_browser_rss_bytes':None,'memory_limitations':'JS heap is not total browser/process memory. No production browser worker capacity claim.'}
        browser.close()
    report={'scope':'Synthetic virtual replay only; no actual live-feed latency benchmark',
            'external_api_calls':0,'actual_external_lag_seconds':None,'actual_external_missed_deliveries':None,
            'actual_external_corrections':None,'budget_example':{'four_hour_30s_polls':480,'100calls_four_hour_min_interval_seconds':144},
            'experiments':[simulate(144),simulate(2,delay=2)],'browser':browser_check,
            'decision':'NO-GO external collector; GO historical replay and rights-authorized local manual input',
            'limitations':'Assumed full event-history snapshots avoid missing final delivery records but many states arrive too late for before-next-ball predictions. Does not prove human scoring latency, provider quality or live permission.'}
    (PROJECT_ROOT/'docs/audit/live-feasibility-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
