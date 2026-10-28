"""Audit tooling using declared virtual-clock fixtures; real cohort remains empty."""
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.events import initial_state,apply_event
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.integrations.collector import LocalCollector,manual_delivery
from criclytics_app.services.forecasts import ForecastService
from criclytics_app.ml.shadow_evaluation import evaluate,MODEL
from tests.test_reconciliation import setup_data,observation,next_context


def main():
    model=PROJECT_ROOT/'build/baseline-v1-first/model.json';evaluation=PROJECT_ROOT/'build/baseline-v1-first/evaluation.json'
    baselines=PROJECT_ROOT/'build/shadow-baselines-v1-final.json';protocol=digest(PROJECT_ROOT/'docs/SHADOW_PROTOCOL.md')
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory);now=[datetime(2026,10,29,10,tzinfo=timezone.utc).timestamp()]
        timestamp=lambda value:datetime.fromtimestamp(value,timezone.utc).isoformat()
        meta,one,_=setup_data();meta['dates']=['2026-10-29'];source=root/'source.sqlite3';ledger=root/'ledger.sqlite3'
        collector=LocalCollector(source,enabled=True,clock=lambda:now[0])
        service=ForecastService(source,ledger,model,MODEL,evaluation,digest(evaluation),clock=lambda:now[0],baselines=baselines,baselines_sha=digest(baselines))
        frozen=datetime.now(timezone.utc).isoformat()
        cohort={'schema_version':1,'protocol_sha256':protocol,'model_id':MODEL,'baseline_sha256':digest(baselines),'frozen_artifacts_at':frozen,'matches':[{'match_id':meta['match_id'],'mode':'manual',
                 'enrolled_at':timestamp(now[0]-1),'rights_confirmed':True,
                 'timing_review':{'reviewer':'AUTHORED-FIXTURE-NOT-HUMAN','method':'virtual clock test only','evidence_ref':'fictional'}}]}
        try:
            initial=initial_state(meta,1)
            collector.ingest(meta,observation(meta,'confirmation',[],next_context(initial,1,'player:a','player:b')))
            issued=service.forecast(meta['match_id']);assert issued['forecast_allowed'],issued
            one['event_time']=timestamp(now[0]+2);now[0]+=3;state=apply_event(initial,one)
            collector.ingest(meta,observation(meta,'one',[one],next_context(state,2)))
            correction=deepcopy(one);correction['revision']=2;correction['runs'].update(batter=2,total=2);now[0]+=1
            state=apply_event(initial_state(meta,1),correction)
            collector.ingest(meta,observation(meta,'correction',[correction],next_context(state,2,'player:a','player:b')))
            service.forecast(meta['match_id'])
            second=manual_delivery(meta,state,'player:a','player:b','player:c',event_time=timestamp(now[0]))
            now[0]+=1;state=apply_event(state,second);collector.ingest(meta,observation(meta,'two',[second],next_context(state,3,'player:a','player:b')))
            third=manual_delivery(meta,state,'player:a','player:b','player:c',event_time=None);now[0]+=1
            collector.ingest(meta,observation(meta,'three',[third],status='completed'))
            path=root/'cohort.json';path.write_text(json.dumps(cohort),encoding='utf-8')
            result=evaluate(source,ledger,path,model,baselines,digest(baselines))
            assert result['scored_attempts']==1,result
            assert result['counts']['late_or_equal_issue']==1 and result['counts']['no_issued_forecast']==1,result
            assert result['counts']['corrected_outcomes']==1 and result['counts']['unknown_actual_start']==1,result
            result['evidence_kind']='AUTHORED_VIRTUAL_CLOCK_FIXTURE_NOT_PROSPECTIVE_COHORT'
            (PROJECT_ROOT/'docs/audit/shadow-tooling-fixture-2026-10-28.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
            path.write_text(json.dumps({**cohort,'matches':[]}),encoding='utf-8')
            pending=evaluate(source,ledger,path,model,baselines,digest(baselines))
            pending['evidence_kind']='ACTUAL_PROSPECTIVE_COHORT_NOT_STARTED'
            pending['baseline_sha256']=digest(baselines)
            (PROJECT_ROOT/'docs/audit/prospective-shadow-2026-10-28.json').write_text(json.dumps(pending,indent=2,allow_nan=False)+'\n',encoding='utf-8')
            print(json.dumps({'fixture_scored':result['scored_attempts'],'fixture_counts':result['counts'],'real_cohort':pending['cohort_status'],'decision':pending['promotion_decision']}))
        finally:collector.close()


if __name__=='__main__':main()
