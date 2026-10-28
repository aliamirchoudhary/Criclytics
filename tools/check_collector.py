"""Bounded agent-run authorized replay sample; not a human/live source benchmark."""
from copy import deepcopy
import json
from pathlib import Path
import time
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.integrations.collector import LocalCollector,read_snapshot
from criclytics_app.pipeline.events import canonicalize,EventStore,replay


def main():
    pack=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))
    metadata,events=canonicalize(pack['fixtures'][1]['match'],'collector-sample')
    path=PROJECT_ROOT/'build/collector-sample-v1.sqlite3';collector=LocalCollector(path,mode='replay',enabled=True)
    samples=[]
    try:
        # Only delivery attempts, no source scorecard/paid endpoint requests.
        for index,event in enumerate((e for e in events if e['kind']=='delivery'),1):
            payload={'schema_version':1,'match_id':metadata['match_id'],'observation_id':'sample-'+str(index),'status':'in_progress','events':[event]}
            start=time.perf_counter();receipt=collector.ingest(metadata,payload)
            assert receipt['status'] in ('accepted','duplicate')
            samples.append({'status':receipt['status'],'milliseconds':round((time.perf_counter()-start)*1000,3)})
        before=collector.guard.execute("SELECT SUM(count) FROM budgets WHERE kind='day'").fetchone()[0]
        for _ in range(100):read_snapshot(path,metadata['match_id'])
        after=collector.guard.execute("SELECT SUM(count) FROM budgets WHERE kind='day'").fetchone()[0]
        assert before==after
        store=EventStore(path)
        try:
            states=replay(metadata,store.events(metadata['match_id']))
            count=store.connection.execute('SELECT COUNT(*) FROM observations').fetchone()[0]
        finally:store.close()
    finally:collector.close()
    result={'source_mode':'replay','fixture':'Authored fictional golden match','observations':count,'ingest_samples':samples,
            'reader_requests':100,'reader_added_collection_cost':after-before,'external_api_calls':0,'dollars':0,'card_required':False,
            'replayed_innings':[{'innings':state['innings'],'runs':state['runs'],'wickets':state['wickets'],'legal_balls':state['legal_balls']} for state in states],
            'actual_human_entry_latency':None,'actual_live_source_lag':None,
            'limitations':'Agent-run local authored replay only. No real human scoring, network uptime or actual live-feed SLA proven.'}
    (PROJECT_ROOT/'docs/audit/local-collector-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
