from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from criclytics_app.ml.shadow_evaluation import timing_reasons,summarize,replay_features,MODEL,REGISTERED
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.services.forecasts import ForecastService
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.pipeline.events import initial_state,apply_event,EventStore,encoded
from tests.test_reconciliation import setup_data,observation,next_context,NOW
from tests.test_forecasts import model_files
from tests.test_baseline import artifact


class ShadowEvaluationTests(unittest.TestCase):
    def test_late_equal_unknown_replay_and_changed_timing_fail(self):
        cohort={'mode':'manual','enrolled_at':'2026-10-29T09:00:00Z','rights_confirmed':True,
                'timing_review':{'reviewer':'fixture-only','method':'authored fixture','evidence_ref':'fictional'}}
        event={'event_time':'2026-10-29T10:00:02Z','observed_at':'2026-10-29T10:00:03Z'}
        entry={'issued_at':'2026-10-29T10:00:01Z','content':{'mode':'manual','source_cutoff':'2026-10-29T10:00:00Z',
               'model_id':MODEL,'protocol_sha256':'protocol','baseline_artifact_sha256':'baseline',
               'baselines':{'empirical':{},'phase_innings':{}}}}
        self.assertEqual(timing_reasons(entry,event,event,cohort,'protocol','baseline'),[])
        late=deepcopy(entry);late['issued_at']=event['event_time']
        self.assertIn('late_or_equal_issue',timing_reasons(late,event,event,cohort,'protocol','baseline'))
        unknown={**event,'event_time':None}
        self.assertIn('unknown_actual_or_original_observation_time',timing_reasons(entry,unknown,event,cohort,'protocol','baseline'))
        self.assertIn('actual_start_changed_by_correction',timing_reasons(entry,{**event,'event_time':'2026-10-29T10:00:05Z'},event,cohort,'protocol','baseline'))
        self.assertIn('not_prospective_manual',timing_reasons(entry,event,event,{**cohort,'mode':'replay'},'protocol','baseline'))

    def test_fixture_metrics_missing_denominator_and_null_empty_cohort(self):
        model=artifact();labels=model['labels'];rows=[]
        for i in (1,2):
            p={labels[0]:.1,labels[i]:.8,labels[3-i]:.1}
            rows.append({'match_id':str(i),'label':labels[i],'innings':1,
                         'features':{'innings':1,'phase_band':0,'prior_batter_samples':0},'learner':p,
                         'empirical':dict.fromkeys(labels,1/3),'phase_innings':dict.fromkeys(labels,1/3)})
        result=summarize(rows,labels,np.array([.1,.45,.45]),Counter(collected_attempts=3,reviewed_start_times=2),[1,2])
        self.assertAlmostEqual(result['metrics']['learner']['log_loss'],-np.log(.8))
        self.assertAlmostEqual(result['collected_attempt_coverage'],2/3)
        self.assertEqual(result['learner_minus_baseline_log_loss_intervals']['empirical']['matches'],2)
        self.assertEqual(result['promotion_decision'],'NO-GO')
        empty=summarize([],labels,np.array([.1,.45,.45]),Counter(),[])
        self.assertIsNone(empty['metrics']['learner']);self.assertIsNone(empty['collected_attempt_coverage'])
        self.assertFalse(empty['gates']['minimum_matches'])
        json.dumps(empty,allow_nan=False)

    def test_baselines_are_preissued_and_raw_receipt_features_reproduce(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model,report=model_files(root);value=json.loads(model.read_text())
            baselines={'schema_version':1,'feature_schema':1,'model_id':digest(model),'dataset_id':'fictional','features_sha256':'fixture',
                       'labels':value['labels'],'prior':[.1,.45,.45],'phase_counts':{},'shrinkage':20,
                       'protocol_sha256':digest(PROJECT_ROOT/'docs/SHADOW_PROTOCOL.md')}
            path=root/'baselines.json';path.write_text(encoded(baselines))
            meta,one,_=setup_data();collector=LocalCollector(root/'source.sqlite3',enabled=True,clock=lambda:NOW)
            try:
                score=apply_event(initial_state(meta,1),one);collector.ingest(meta,observation(meta,'first',[one],next_context(score,2)))
                service=ForecastService(root/'source.sqlite3',root/'ledger.sqlite3',model,digest(model),report,digest(report),clock=lambda:NOW,
                                        baselines=path,baselines_sha=digest(path))
                result=service.forecast(meta['match_id']);self.assertEqual(set(result['forecast']['content']['baselines']),{'empirical','phase_innings'})
                store=EventStore(root/'source.sqlite3',readonly=True)
                try:self.assertEqual(replay_features(store,result['core']),result['core']['features'])
                finally:store.close()
                self.assertEqual(service.forecast(meta['match_id'])['forecast'],result['forecast'])
            finally:collector.close()


if __name__=='__main__':unittest.main()
