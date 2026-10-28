from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from criclytics_app.services.match_context import ContextLedger
from criclytics_app.services.annotations import annotation_context


def annotation(identifier='drop',occurred=True):
    return {'schema_version':1,'record_id':identifier,'revision':1,'match_id':'match:fixture','kind':'fielding',
            'source':'authored fictional match','observer':'observer-a','published_at':'2020-01-01T10:00:01Z',
            'observed_at':'2020-01-01T10:00:02Z','effective_at':'2020-01-01T10:00:01Z','scope':'public',
            'value':{'event_id':'match:fixture#i1/d1','annotation_kind':'dropped_catch','occurred':occurred,
                     'confidence':'observed','review_state':'reviewed','reviewer':'fixture reviewer','event_time':'2020-01-01T10:00:00Z','player_id':None}}


class AnnotationTests(unittest.TestCase):
    def test_missing_false_and_current_target_are_distinct(self):
        self.assertIsNone(annotation_context([],'match:fixture#i1/d2')['confirmed_drops'])
        record=annotation(occurred=False)
        self.assertEqual(annotation_context([record],'match:fixture#i1/d2')['confirmed_drops'],0)
        self.assertIsNone(annotation_context([record],'match:fixture#i1/d1')['confirmed_drops'])

    def test_backfill_conflict_correction_and_private_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=ContextLedger(Path(directory)/'annotations.sqlite3')
            try:
                first=annotation();ledger.add(first)
                other=annotation('other',False);other['observer']='observer-b';ledger.add(other)
                records=ledger.eligible('match:fixture','2020-01-01T10:01:00Z')
                self.assertIsNone(annotation_context(records,'match:fixture#i1/d2')['confirmed_drops'])
                revised=deepcopy(other);revised['revision']=2;revised['value']['occurred']=True;revised['observed_at']='2020-01-01T11:00:00Z';ledger.add(revised)
                self.assertIsNone(annotation_context(ledger.eligible('match:fixture','2020-01-01T10:30:00Z'),'match:fixture#i1/d2')['confirmed_drops'])
                self.assertEqual(annotation_context(ledger.eligible('match:fixture','2020-01-01T11:01:00Z'),'match:fixture#i1/d2')['confirmed_drops'],1)
                private=annotation('private');private['scope']='private';private['owner_id']='coach-a';ledger.add(private)
                self.assertEqual(len(ledger.eligible('match:fixture','2020-01-01T11:01:00Z')),2)
                self.assertEqual(len(ledger.eligible('match:fixture','2020-01-01T11:01:00Z',owner_id='coach-b')),2)
                self.assertEqual(len(ledger.eligible('match:fixture','2020-01-01T11:01:00Z',owner_id='coach-a')),3)
                bad=annotation('bad');bad['value']['private_notes']='sensitive tactical plan'
                with self.assertRaises(ValueError):ledger.add(bad)
                self.assertEqual(ledger.connection.execute('SELECT COUNT(*) FROM context_records').fetchone()[0],4)
            finally:ledger.close()

    def test_actor_uncertainty_does_not_double_count_one_chance(self):
        first=annotation();second=annotation('identified');second['value']['player_id']='player:fixture:fielder'
        result=annotation_context([first,second],'match:fixture#i1/d2')
        self.assertEqual(result['confirmed_drops'],1);self.assertEqual(len(result['observations']),1)
