from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.events import canonicalize,EventStore,encoded,initial_state,apply_event
from criclytics_app.pipeline.features import vector,History,LocalHistory,outcome,label,generate,partitions

PACK=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


class FeatureTests(unittest.TestCase):
    def test_hand_vector_excludes_target_and_preserves_joint_outcome(self):
        metadata,events=canonicalize(PACK['fixtures'][1]['match'],'fixture')
        event=next(e for e in events if e['kind']=='delivery')
        state=initial_state(metadata,1);history=History();local=LocalHistory()
        first=vector(state,event,history,local,metadata)
        self.assertEqual(first['runs'],0);self.assertIsNone(first['run_rate']);self.assertIsNone(first['prior_matchup_wicket_rate'])
        self.assertIsNone(first['target']);self.assertIsNone(first['balls_remaining'])
        history.observe(event);local.observe(event);apply_event(state,event)
        second=vector(state,event,history,local,metadata)
        self.assertEqual(second['runs'],event['runs']['total']);self.assertEqual(second['prior_batter_samples'],1)
        result=deepcopy(event);result['runs']={'batter':1,'extras':1,'total':2};result['extras']={'noballs':1};result['wickets']=[{'kind':'run out','player_id':'p','player_out':'P'}]
        joint=outcome(result)
        self.assertEqual(joint['total_runs'],2);self.assertFalse(joint['legal']);self.assertEqual(joint['dismissals'],['run out'])
        self.assertEqual(joint['total_runs'],joint['batter_runs']+sum(joint['extras'].values()))
        self.assertNotEqual(label(event),label(result))

    def rows(self,folder,change_day=None,change_attempt=None):
        store=EventStore(Path(folder)/'events.sqlite3')
        try:
            for day in range(1,7):
                raw=deepcopy(PACK['fixtures'][1]['match']);raw['info']['dates']=['2020-01-0'+str(day)]
                names=sum(raw['info']['players'].values(),[]);raw['info']['registry']={'people':{name:'id'+str(i) for i,name in enumerate(names)}}
                if day==change_day:
                    deliveries=[d for innings in raw['innings'] for over in innings['overs'] for d in over['deliveries']]
                    selected=deliveries[change_attempt or 0];selected['runs']['batter']+=2;selected['runs']['total']+=2
                metadata,events=canonicalize(raw,str(day));store.ingest(raw,metadata,events)
            return [row for row,split in generate(store)]
        finally:store.close()

    def test_future_match_and_target_perturbation_and_chronological_split(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b,tempfile.TemporaryDirectory() as c:
            base=self.rows(a);future=self.rows(b,6);target=self.rows(c,1,1)
            prefix=[r for r in base if r['match_start_date']<'2020-01-06']
            self.assertEqual(prefix,[r for r in future if r['match_start_date']<'2020-01-06'])
            first=[r for r in base if r['match_id']=='match:cricsheet:1'];changed=[r for r in target if r['match_id']=='match:cricsheet:1']
            self.assertEqual(first[0]['features'],changed[0]['features']);self.assertEqual(first[1]['features'],changed[1]['features'])
            assignments={}
            for row in base:
                assignments.setdefault(row['match_id'],set()).add(row['partition'])
                if row['history_cutoff_date']:self.assertLess(row['history_cutoff_date'],row['match_start_date'])
            self.assertTrue(all(len(v)==1 for v in assignments.values()))
            self.assertEqual({r['partition'] for r in base},{'train','calibration','test'})
            digest=lambda rows:hashlib.sha256(encoded(rows).encode()).hexdigest()
            self.assertEqual(digest(prefix),digest([r for r in future if r['match_start_date']<'2020-01-06']))

    def test_same_day_not_split_and_multiday_overlap_rejected(self):
        metadata=[{'match_id':str(i),'dates':['2020-01-0'+str(i)]} for i in range(1,7)]
        metadata.append({'match_id':'same-day','dates':['2020-01-03']})
        assignment,_=partitions(metadata)
        self.assertEqual(assignment['3'],assignment['same-day'])
        metadata[2]['dates'].append('2020-01-05')
        with self.assertRaises(ValueError):partitions(metadata)
