"""One real historical match streamed through the permitted replay adapter; no live SLA claim."""
from collections import defaultdict
import json
from pathlib import Path
import tempfile
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.events import canonicalize,initial_state,apply_event
from criclytics_app.pipeline.features import History,LocalHistory,vector
from criclytics_app.pipeline.scoring import score_match
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.services.reconciliation import Reconciler


def main():
    raw=json.loads((PROJECT_ROOT/'data/raw/t20s_male_json/1001349.json').read_text(encoding='utf-8'))
    meta,events=canonicalize(raw,'1001349');now=[1577872800.0];checks=[]
    states={i['innings']:initial_state(meta,i['innings']) for i in meta['innings']};locals={i:LocalHistory() for i in states}
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'stream.sqlite3';collector=LocalCollector(path,mode='replay',enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0])
        pending=[];frame=0
        try:
            for event in events:
                innings=event['innings'];state=states[innings]
                if event['kind']=='delivery':
                    frame+=1
                    context={'innings':innings,'attempt':event['attempt'],'striker':event['striker'],'non_striker':event['non_striker'],'bowler':event['bowler'],
                             'not_started_confirmed':True,'expected_state':{key:state[key] for key in ('runs','wickets','legal_balls')}}
                    body={'schema_version':1,'match_id':meta['match_id'],'observation_id':'frame-'+str(frame),'status':'in_progress','events':pending,'next_context':context}
                    receipt=collector.ingest(meta,body);assert receipt['status']=='accepted'
                    result=service.get(meta['match_id']);assert result['forecast_allowed'],(frame,result['blocked_reasons'])
                    expected=vector(state,context,History(),locals[innings],meta)
                    assert result['core']['features']==expected,(frame,result['core']['features'],expected)
                    checks.append({'innings':innings,'attempt':event['attempt'],'state_id':result['state_id']})
                    pending=[];locals[innings].observe(event)
                apply_event(state,event);pending.append(event);now[0]+=2
            final={'schema_version':1,'match_id':meta['match_id'],'observation_id':'completed','status':'completed','events':pending,'next_context':None}
            collector.ingest(meta,final);result=service.get(meta['match_id']);assert not result['forecast_allowed']
            expected=score_match(raw)['innings']
            for got,want in zip(result['core']['innings'],expected):
                assert (got['runs'],got['wickets'],got['legal_balls'])==(want['total'],want['wickets'],want['legal_balls'])
            rebuilds=service.rebuilds
            for _ in range(100):service.get(meta['match_id'])
            assert service.rebuilds==rebuilds
        finally:collector.close()
    report={'mode':'replay','source':'Cricsheet ODC-BY-1.0 historical match1001349','virtual_clock':True,'external_calls':0,
            'before_attempt_vectors_verified':len(checks),'all_vectors_equal':True,'completed_score_reconciled':True,
            'repeat_readers':100,'repeat_rebuilds':0,'state_fingerprints':checks,'terminal_blocked_reasons':result['blocked_reasons'],
            'correction_revision_tests':'Portable tests cover gaps/reorder/tombstones/corrections/target/schedule/metadata append and immutable forecast replacement.',
            'limitations':'Recorded historical replay emulates source arrival; no actual live provider, human accuracy, exact historical availability or SLA proved.'}
    (PROJECT_ROOT/'docs/audit/stream-parity-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
