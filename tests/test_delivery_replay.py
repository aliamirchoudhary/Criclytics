from copy import deepcopy
import json
from pathlib import Path
import random
import tempfile
import unittest
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.events import canonicalize,EventStore,replay,checksum,apply_event,initial_state,validate_event
from criclytics_app.pipeline.scoring import score_match

PACK=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


class ReplayTests(unittest.TestCase):
    def test_golden_score_conservation_duplicate_and_reorder(self):
        with tempfile.TemporaryDirectory() as directory:
            store=EventStore(Path(directory)/'events.sqlite3')
            try:
                for fixture in PACK['fixtures']:
                    metadata,events=canonicalize(fixture['match'],fixture['id'])
                    shuffled=deepcopy(events);random.Random(17).shuffle(shuffled)
                    store.ingest(fixture['match'],metadata,shuffled)
                    store.ingest(fixture['match'],metadata,events)
                    actual=replay(metadata,store.events(metadata['match_id']))
                    expected=score_match(fixture['match'])['innings']
                    self.assertEqual(len(actual),len(expected))
                    for got,want in zip(actual,expected):
                        self.assertEqual((got['runs'],got['wickets'],got['legal_balls']),(want['total'],want['wickets'],want['legal_balls']))
                    self.assertTrue(all(e['event_time'] is None and e['observed_at'] is None for e in events))
                self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM observations').fetchone()[0],5)
            finally:store.close()

    def test_correction_tombstone_strike_target_and_illegal_attempt(self):
        raw=deepcopy(PACK['fixtures'][1]['match']);metadata,events=canonicalize(raw,'fixture')
        deliveries=[e for e in events if e['kind']=='delivery']
        state=initial_state(metadata,1)
        for event in deliveries[:2]:apply_event(state,event)
        self.assertEqual(state['attempts'],2)
        self.assertLessEqual(state['legal_balls'],state['attempts'])
        one=deepcopy(deliveries[0]);one['wickets']=[];one['extras']={};one['runs']={'batter':1,'extras':0,'total':1};one['over_end']=False
        state=apply_event(initial_state(metadata,1),one)
        self.assertEqual(state['striker_after'],one['non_striker'])
        with tempfile.TemporaryDirectory() as directory:
            store=EventStore(Path(directory)/'events.sqlite3')
            try:
                store.ingest(raw,metadata,events)
                original=replay(metadata,store.events(metadata['match_id']))[0]['runs']
                revised=deepcopy(deliveries[0]);revised['revision']=2
                revised['runs']['batter']+=2;revised['runs']['total']+=2
                observation={'correction':'fictional','event':revised['event_id']}
                revised['source_hash']=checksum(observation);revised['observed_at']='2026-01-01T00:00:00+00:00'
                store.ingest(observation,metadata,[revised],source='manual',observed_at=revised['observed_at'])
                self.assertEqual(replay(metadata,store.events(metadata['match_id']))[0]['runs'],original+2)
                self.assertEqual(replay(metadata,store.events(metadata['match_id'],as_of='2025-12-31T23:59:59+00:00'))[0]['runs'],original)
                self.assertEqual(list(store.events(metadata['match_id'],as_of='2025-12-31T23:59:59+00:00',allow_unknown=False)),[])
                conflicting=deepcopy(revised);conflicting['runs']['batter']+=1;conflicting['runs']['total']+=1
                with self.assertRaises(ValueError):store.ingest(observation,metadata,[conflicting])
                target={'schema_version':1,'match_id':metadata['match_id'],'innings':2,'attempt':1,'order':9,'kind':'target_revision',
                        'runs':45,'event_id':metadata['match_id']+'/target','revision':1,'source_hash':checksum({'target':45}),
                        'observed_at':'2026-01-01T00:00:01+00:00','event_time':None,'deleted':False}
                store.ingest({'target':45},metadata,[target],source='manual',observed_at=target['observed_at'])
                second=replay(metadata,store.events(metadata['match_id']))[1]
                self.assertEqual(second['target'],45);self.assertTrue(second['target_verified'])
                tombstone=deepcopy(revised);tombstone['revision']=3;tombstone['deleted']=True
                store.ingest(observation,metadata,[tombstone])
                self.assertNotIn(revised['event_id'],[e['event_id'] for e in store.events(metadata['match_id'])])
                self.assertGreater(store.connection.execute('SELECT COUNT(*) FROM events').fetchone()[0],len(events))
            finally:store.close()
        invalid=deepcopy(one);invalid['runs']['total']+=1
        with self.assertRaises(ValueError):validate_event(invalid)
