from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.pipeline.events import canonicalize,EventStore

PACK=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


def fixture():
    metadata,events=canonicalize(PACK['fixtures'][1]['match'],'collector-fixture')
    return metadata,[e for e in events if e['kind']=='delivery']


def payload(meta,event,index):
    return {'schema_version':1,'match_id':meta['match_id'],'observation_id':'observation-'+str(index),'status':'in_progress','events':[event]}


class CollectorTests(unittest.TestCase):
    def test_idempotency_budgets_capture_time_kill_and_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            now=[1000.0];meta,events=fixture();collector=LocalCollector(Path(directory)/'events.sqlite3',mode='replay',enabled=True,clock=lambda:now[0],minute_limit=1,day_limit=2)
            try:
                one=payload(meta,events[0],1)
                with patch('requests.get') as upstream:
                    self.assertEqual(collector.ingest(meta,one)['status'],'accepted')
                    self.assertEqual(collector.ingest(meta,one)['status'],'duplicate');upstream.assert_not_called()
                self.assertEqual(collector.ingest(meta,payload(meta,events[1],2))['reason'],'minute_budget_exhausted')
                now[0]+=61;self.assertTrue(collector.snapshot(meta['match_id'])['stale'])
                self.assertEqual(collector.ingest(meta,payload(meta,events[1],2))['status'],'accepted')
                self.assertEqual(collector.ingest(meta,payload(meta,events[2],3))['reason'],'minute_budget_exhausted')
                now[0]+=61;self.assertEqual(collector.ingest(meta,payload(meta,events[2],3))['reason'],'day_budget_exhausted')
                self.assertEqual(collector.snapshot(meta['match_id'])['source_health'],'budget_exhausted')
                collector.kill();self.assertEqual(collector.ingest(meta,one)['reason'],'disabled_or_killed')
                self.assertTrue(collector.snapshot(meta['match_id'])['killed']);collector.kill(False)
                changed=deepcopy(one);changed['status']='paused'
                with self.assertRaises(ValueError):collector.ingest(meta,changed)
                store=EventStore(collector.path)
                try:
                    rows=list(store.events(meta['match_id']));self.assertEqual(len(rows),2)
                    self.assertEqual(rows[0]['observed_at'],'1970-01-01T00:16:40+00:00')
                    self.assertIsNone(rows[0]['event_time'])
                finally:store.close()
            finally:collector.close()

    def test_two_workers_crash_lease_preserves_capture_and_bounds_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            meta,events=fixture();path=Path(directory)/'events.sqlite3';now=[1000.0]
            first=LocalCollector(path,mode='replay',enabled=True,clock=lambda:now[0])
            try:
                one=payload(meta,events[0],1);reserved=first._reserve(meta,one);self.assertEqual(reserved['status'],'reserved')
                second=LocalCollector(path,mode='replay',enabled=True,clock=lambda:now[0])
                try:
                    self.assertEqual(second.ingest(meta,one)['status'],'deferred')
                    now[0]+=31;self.assertEqual(second.ingest(meta,one)['status'],'accepted')
                    self.assertEqual(second.guard.execute("SELECT SUM(count) FROM budgets WHERE kind='day'").fetchone()[0],2)
                    self.assertEqual(second.ingest(meta,one)['status'],'duplicate')
                finally:second.close()
            finally:first.close()

    def test_parallel_workers_preserve_one_observation_and_no_network(self):
        with tempfile.TemporaryDirectory() as directory:
            meta,events=fixture();path=Path(directory)/'events.sqlite3';barrier=threading.Barrier(2)
            def worker():
                collector=LocalCollector(path,mode='replay',enabled=True)
                try:barrier.wait();return collector.ingest(meta,payload(meta,events[0],1))['status']
                finally:collector.close()
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:worker(),range(2)))
            self.assertIn('accepted',results)
            store=EventStore(path)
            try:self.assertEqual(len(list(store.events(meta['match_id']))),1)
            finally:store.close()

    def test_failure_backoff_and_unapproved_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            meta,events=fixture();now=[1000.0];collector=LocalCollector(Path(directory)/'events.sqlite3',mode='replay',enabled=True,clock=lambda:now[0],day_limit=2)
            try:
                bad=deepcopy(events[0]);bad['runs']['total']+=1
                with self.assertRaises(ValueError):collector.ingest(meta,payload(meta,bad,1))
                self.assertFalse(collector.snapshot(meta['match_id'])['available'])
                self.assertEqual(collector.ingest(meta,payload(meta,events[0],2))['status'],'deferred')
                now[0]+=6;self.assertEqual(collector.ingest(meta,payload(meta,events[0],2))['status'],'accepted')
                self.assertEqual(collector.ingest(meta,payload(meta,bad,1))['reason'],'day_budget_exhausted')
                with self.assertRaises(ValueError):LocalCollector(Path(directory)/'other.sqlite3',mode='external-api',enabled=True)
            finally:collector.close()

    def test_readers_do_not_collect_and_worker_cannot_raise_shared_budget(self):
        from criclytics_app.integrations.collector import read_snapshot,manual_session,manual_delivery
        from criclytics_app.pipeline.events import initial_state
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'manual.sqlite3';meta=manual_session('test','Team A','Team B','2020-01-01')
            event=manual_delivery(meta,initial_state(meta,1),'player:a','player:b','player:c',batter_runs=1)
            first=LocalCollector(path,enabled=True,minute_limit=1)
            try:
                self.assertEqual(first.ingest(meta,payload(meta,event,1))['status'],'accepted')
                for _ in range(100):self.assertEqual(read_snapshot(path,meta['match_id'])['mode'],'manual')
                second=LocalCollector(path,enabled=True,minute_limit=60)
                try:self.assertEqual(second.ingest(meta,payload(meta,event,2))['reason'],'minute_budget_exhausted')
                finally:second.close()
                self.assertEqual(first.guard.execute("SELECT SUM(count) FROM budgets WHERE kind='day'").fetchone()[0],1)
            finally:first.close()
