from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from criclytics_app.services.match_context import ContextLedger,lineup_snapshot,pitch_context,venue_affiliation
from criclytics_app.pipeline.features import History,LocalHistory,vector
from criclytics_app.pipeline.events import canonicalize,initial_state
import json
from criclytics_app.paths import PROJECT_ROOT
PACK=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


def record(kind,identifier,value):
    return {'schema_version':1,'record_id':identifier,'revision':1,'match_id':'match:fixture','kind':kind,'source':'fictional source','observer':'fixture-author',
            'published_at':'2020-01-01T10:00:00Z','observed_at':'2020-01-01T10:01:00Z','effective_at':'2020-01-01T10:00:00Z','scope':'public','value':value}


class ContextTests(unittest.TestCase):
    def test_late_xi_substitution_and_immutable_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=ContextLedger(Path(directory)/'context.sqlite3')
            try:
                xi=record('lineup','xi',{'team_id':'team:a','player_ids':['player:'+str(i) for i in range(11)],'roles':{'player:0':'captain'}})
                ledger.add(xi);ledger.add(xi)
                self.assertFalse(lineup_snapshot(ledger.eligible('match:fixture','2020-01-01T10:00:30Z'),'team:a')['available'])
                sub=record('substitution','sub',{'team_id':'team:a','out_id':'player:0','in_id':'player:12','role':'replacement'})
                sub['observed_at']='2020-01-01T11:00:00Z';sub['effective_at']='2020-01-01T10:30:00Z';ledger.add(sub)
                self.assertIn('player:0',lineup_snapshot(ledger.eligible('match:fixture','2020-01-01T10:45:00Z'),'team:a')['players'])
                after=lineup_snapshot(ledger.eligible('match:fixture','2020-01-01T11:01:00Z'),'team:a');self.assertIn('player:12',after['players']);self.assertNotIn('player:0',after['players'])
                conflicting=deepcopy(xi);conflicting['value']['roles']={}
                with self.assertRaises(ValueError):ledger.add(conflicting)
                self.assertEqual(ledger.connection.execute('SELECT COUNT(*) FROM context_records').fetchone()[0],2)
            finally:ledger.close()

    def test_pitch_missing_tracking_and_explicit_home_context(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=ContextLedger(Path(directory)/'context.sqlite3')
            try:
                pitch=record('pitch_report','pitch',{'venue_id':'venue:a','quality':'observer_report','tags':['dry']});ledger.add(pitch)
                rows=ledger.eligible('match:fixture','2020-01-01T11:00:00Z')
                self.assertIsNone(pitch_context(rows,'venue:a')['measurements']);self.assertEqual(venue_affiliation(rows,'venue:a','team:a')['status'],'unknown')
                bad=deepcopy(pitch);bad['value']['bounce_cm']=60
                with self.assertRaises(ValueError):ledger.add(bad)
                home=record('venue_affiliation','home',{'venue_id':'venue:a','team_id':'team:a','status':'neutral'});ledger.add(home)
                self.assertEqual(venue_affiliation(ledger.eligible('match:fixture','2020-01-01T11:00:00Z'),'venue:a','team:a')['status'],'neutral')
            finally:ledger.close()

    def test_sparse_matchup_shrinks_to_empirical_prior(self):
        meta,events=canonicalize(PACK['fixtures'][1]['match'],'fixture');event=next(e for e in events if e['kind']=='delivery')
        history=History();history.global_count=100;history.global_wickets=10;history.global_runs=120
        history.matchups[(event['striker'],event['bowler'])]=[1,0,1]
        values=vector(initial_state(meta,1),event,history,LocalHistory(),meta)
        self.assertEqual(values['prior_matchup_samples'],1);self.assertAlmostEqual(values['prior_matchup_wicket_rate'],(1+20*.1)/21)
