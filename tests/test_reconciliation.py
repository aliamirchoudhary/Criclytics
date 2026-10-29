from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import tempfile
import unittest
from criclytics_app.integrations.collector import LocalCollector,manual_session,manual_delivery
from criclytics_app.pipeline.events import initial_state,apply_event,EventStore
from criclytics_app.pipeline.features import History,LocalHistory,vector
from criclytics_app.services.reconciliation import Reconciler,StateLedger

NOW=datetime(2020,1,1,10,tzinfo=timezone.utc).timestamp()


def setup_data():
    meta=manual_session('fixture','Team A','Team B','2020-01-01',gender='male',team_type='international')
    state=initial_state(meta,1);one=manual_delivery(meta,state,'player:a','player:b','player:c',batter_runs=1)
    apply_event(state,one)
    two=manual_delivery(meta,state,'player:b','player:a','player:c',batter_runs=0)
    return meta,one,two


def next_context(state,attempt,striker='player:b',non_striker='player:a',bowler='player:c'):
    return {'innings':state['innings'],'attempt':attempt,'striker':striker,'non_striker':non_striker,'bowler':bowler,
            'not_started_confirmed':True,'expected_state':{key:state[key] for key in ('runs','wickets','legal_balls')}}


def observation(meta,identifier,events,context=None,status='in_progress'):
    return {'schema_version':1,'match_id':meta['match_id'],'observation_id':identifier,'events':events,'status':status,'next_context':context}


class ReconciliationTests(unittest.TestCase):
    def test_shared_vector_correction_and_issued_forecast_immutability(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite3';now=[NOW];meta,one,two=setup_data()
            collector=LocalCollector(path,enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0]);ledger=StateLedger(Path(directory)/'states.sqlite3')
            try:
                state=apply_event(initial_state(meta,1),one);context=next_context(state,2)
                collector.ingest(meta,observation(meta,'one',[one],context))
                first=service.get(meta['match_id']);self.assertTrue(first['forecast_allowed'],first['blocked_reasons'])
                local=LocalHistory();local.observe(one)
                self.assertEqual(first['core']['features'],vector(state,context,History(),local,meta))
                first_id=ledger.record(first['core']);content={'match_id':meta['match_id'],'target_event_id':first['core']['target_event_id'],'state_id':first_id,'model_id':'fixture-model','distribution':{'fixture-only':1}}
                issued=ledger.issue(content,'2020-01-01T10:00:00Z');old_payload=deepcopy(issued)
                corrected=deepcopy(one);corrected['revision']=2;corrected['runs']['batter']=2;corrected['runs']['total']=2
                now[0]+=1;changed=apply_event(initial_state(meta,1),corrected)
                update=observation(meta,'correction',[corrected],next_context(changed,2,striker='player:a',non_striker='player:b'))
                collector.ingest(meta,update);second=service.get(meta['match_id']);self.assertTrue(second['forecast_allowed'])
                second_id=ledger.record(second['core']);self.assertNotEqual(first_id,second_id)
                replacement=ledger.issue({**content,'state_id':second_id},'2020-01-01T10:00:01Z')
                self.assertEqual(replacement['replaces_forecast_id'],issued['forecast_id']);self.assertEqual(ledger.forecast(issued['forecast_id']),old_payload)
                collector.ingest(meta,update);self.assertEqual(service.get(meta['match_id'])['state_id'],second_id)
                self.assertEqual(service.rebuilds,2)
                now[0]+=16;expired=service.get(meta['match_id']);self.assertFalse(expired['forecast_allowed']);self.assertIn('next_announcement_expired',expired['blocked_reasons'])
                ledger.record(expired['core'],expired['blocked_reasons']);self.assertEqual(ledger.forecast(issued['forecast_id']),old_payload)
                with self.assertRaises(ValueError):ledger.issue({**content,'distribution':{'changed':1}},'2020-01-01T10:00:19Z')
            finally:collector.close();ledger.close()

    def test_reorder_gap_tombstone_reconnect_and_contradiction(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite3';now=[NOW];meta,one,two=setup_data();collector=LocalCollector(path,enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0])
            try:
                final=apply_event(apply_event(initial_state(meta,1),one),two);context=next_context(final,3)
                collector.ingest(meta,observation(meta,'two-first',[two],context));self.assertIn('missing_delivery_attempt',service.get(meta['match_id'])['blocked_reasons'])
                now[0]+=1;collector.ingest(meta,observation(meta,'one-later',[one],context));self.assertTrue(service.get(meta['match_id'])['forecast_allowed'])
                bad=deepcopy(context);bad['expected_state']['runs']=99
                now[0]+=1;collector.ingest(meta,observation(meta,'bad-confirmation',[],bad));self.assertIn('announced_score_conflict',service.get(meta['match_id'])['blocked_reasons'])
                now[0]+=1;deleted=deepcopy(one);deleted['revision']=2;deleted['deleted']=True
                after=apply_event(initial_state(meta,1),two);collector.ingest(meta,observation(meta,'delete',[deleted],next_context(after,3)))
                current=service.get(meta['match_id']);self.assertTrue(current['forecast_allowed'],current['blocked_reasons']);self.assertEqual(current['core']['features']['attempts'],1)
                now[0]+=61;self.assertIn('stale_source',service.get(meta['match_id'])['blocked_reasons'])
                collector.ingest(meta,observation(meta,'reconnected',[],next_context(after,3)));self.assertTrue(service.get(meta['match_id'])['forecast_allowed'])
                collector.ingest(meta,observation(meta,'abandoned',[],status='abandoned'));self.assertIn('source_abandoned',service.get(meta['match_id'])['blocked_reasons'])
            finally:collector.close()

    def test_innings_end_target_schedule_and_metadata_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite3';now=[NOW];meta,one,two=setup_data();collector=LocalCollector(path,enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0])
            try:
                apply_event(initial_state(meta,1),one)
                closing={'schema_version':1,'match_id':meta['match_id'],'event_id':meta['match_id']+'#i1/innings_end','innings':1,'attempt':2,'order':22,'kind':'innings_end','revision':1,'runs':1,'wickets':0,'legal_balls':1,'source_hash':'assigned-at-ingest','observed_at':None,'event_time':None,'deleted':False}
                collector.ingest(meta,observation(meta,'close',[one,closing],status='innings_break'))
                second=initial_state(meta,2);context=next_context(second,1,'player:d','player:e','player:a')
                target={**closing,'event_id':meta['match_id']+'#i2/target','innings':2,'attempt':1,'order':9,'kind':'target_revision','runs':2}
                schedule={**target,'event_id':meta['match_id']+'#i2/schedule','order':8,'kind':'schedule_revision','runs':6}
                now[0]+=1;collector.ingest(meta,observation(meta,'chase',[target,schedule],context))
                result=service.get(meta['match_id']);self.assertTrue(result['forecast_allowed'],result['blocked_reasons']);self.assertEqual(result['core']['features']['target'],2);self.assertEqual(result['core']['features']['balls_remaining'],6)
                rain={**target,'revision':2,'runs':3};now[0]+=1;collector.ingest(meta,observation(meta,'rain',[rain],context,status='paused'))
                self.assertIn('source_paused',service.get(meta['match_id'])['blocked_reasons'])
                now[0]+=1;collector.ingest(meta,observation(meta,'resume',[],context));self.assertEqual(service.get(meta['match_id'])['core']['features']['target'],3)
                expanded=deepcopy(meta)
                expanded['innings'] += [{**deepcopy(meta['innings'][0]),'innings':3,'super_over':True},{**deepcopy(meta['innings'][1]),'innings':4,'super_over':True}]
                update=observation(expanded,'extra-innings',[],context);update['metadata_revision']=2;now[0]+=1;collector.ingest(expanded,update)
                store=EventStore(path,readonly=True)
                try:
                    self.assertEqual(len(store.metadata(meta['match_id'])['innings']),4)
                    self.assertEqual(len(store.metadata(meta['match_id'],as_of='2020-01-01T10:00:00Z')['innings']),2)
                finally:store.close()
            finally:collector.close()

    def test_distinct_duplicate_observations_keep_first_canonical_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite3';now=[NOW];meta,one,_=setup_data();collector=LocalCollector(path,enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0])
            try:
                state=apply_event(initial_state(meta,1),one);context=next_context(state,2)
                collector.ingest(meta,observation(meta,'first',[one],context));first=service.get(meta['match_id'])
                now[0]+=1;collector.ingest(meta,observation(meta,'reobserved',[one],context));second=service.get(meta['match_id'])
                self.assertTrue(second['forecast_allowed']);self.assertEqual(first['core']['features'],second['core']['features'])
                store=EventStore(path,readonly=True)
                try:
                    events=list(store.events(meta['match_id']));self.assertEqual(len(events),1)
                    self.assertEqual(events[0]['observed_at'],'2020-01-01T10:00:00+00:00')
                    self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM observations').fetchone()[0],2)
                finally:store.close()
            finally:collector.close()

    def test_late_reserved_correction_invalidates_cached_old_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'events.sqlite3';now=[NOW];meta,one,_=setup_data();collector=LocalCollector(path,enabled=True,clock=lambda:now[0]);service=Reconciler(path,clock=lambda:now[0]);ledger=StateLedger(Path(directory)/'states.sqlite3')
            try:
                state=apply_event(initial_state(meta,1),one);context=next_context(state,2)
                collector.ingest(meta,observation(meta,'original',[one],context));original=service.get(meta['match_id']);ledger.record(original['core'])
                corrected=deepcopy(one);corrected['revision']=2;corrected['runs']['batter']=2;corrected['runs']['total']=2
                changed=apply_event(initial_state(meta,1),corrected);correct_context=next_context(changed,2,'player:a','player:b')
                pending=observation(meta,'reserved-correction',[corrected],correct_context);now[0]+=1;collector._reserve(meta,pending)
                now[0]+=31;collector.ingest(meta,observation(meta,'newer-confirmation',[],context))
                self.assertFalse(service.get(meta['match_id'])['forecast_allowed'])
                collector.ingest(meta,pending);bad=service.get(meta['match_id']);self.assertIn('announced_score_conflict',bad['blocked_reasons'])
                now[0]+=1;collector.ingest(meta,observation(meta,'correct-confirmation',[],correct_context));latest=service.get(meta['match_id']);self.assertTrue(latest['forecast_allowed'])
                latest_id=ledger.record(latest['core']);ledger.record(original['core'])
                self.assertEqual(ledger.connection.execute('SELECT state_id FROM current_state').fetchone()[0],latest_id)
            finally:collector.close();ledger.close()
