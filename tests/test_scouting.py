from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from criclytics_app import create_app
from criclytics_app.services.json_io import atomic_json
from criclytics_app.pipeline.events import EventStore, canonicalize
from criclytics_app.pipeline.scouting import build
from tests import test_player_id_stats as fixtures


class ScoutingTests(unittest.TestCase):
    def test_identity_report_missing_slices_and_no_private_input(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);store,name,pid,_=fixtures.PlayerIdentityStatsTests().candidate(root)
            atomic_json(root/'coverage.json',{'accepted_matches':3,'first_match_date':'2020-01-01','last_match_date':'2020-01-03'})
            app=create_app({'TESTING':True,'LIVE_DIR':root/'live','REDIS_URL':'','LIVE_FETCH_ENABLED':False,
                            'PROCESSED_DIR':root,'IDENTITY_REGISTRY':root/'identities.json','IDENTITY_PLAYER_STORE':root,'SCOUTING_SAMPLE':''})
            client=app.test_client();params={'player':pid,'format':'Test','opponent':'Unknown Team','venue':'Unknown Ground'}
            response=client.get('/api/v1/scouting',query_string=params)
            self.assertEqual(response.status_code,200);report=response.json
            self.assertEqual(report['player']['identity_id'],pid)
            self.assertIsNone(report['against_opponent']);self.assertIsNone(report['at_venue']);self.assertIsNone(report['matchup'])
            self.assertEqual(report['batting'],store.profile(pid)['batting']['Test'])
            self.assertEqual(report['report_id'],client.get('/api/v1/scouting',query_string=params).json['report_id'])
            self.assertEqual(client.get('/api/v1/scouting',query_string={'player':name}).status_code,409)
            self.assertEqual(client.get('/api/v1/scouting',query_string={**params,'notes':'private'}).status_code,400)
            self.assertEqual(client.post('/api/v1/scouting',json={'notes':'private'}).status_code,405)
            app.extensions['player_id_store']=None
            self.assertEqual(client.get('/api/v1/scouting',query_string=params).status_code,503)

    def test_bounded_offline_sample_counts_source_ids_and_determinism(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=deepcopy(fixtures.PACK['fixtures'][0]['match']);names=sum(raw['info']['players'].values(),[])
            raw['info']['registry']={'people':{name:'id'+str(i) for i,name in enumerate(names)}}
            source=root/'events.sqlite3';store=EventStore(source)
            try:
                meta,events=canonicalize(raw,'fixture');store.ingest(raw,meta,events)
                store.connection.execute('CREATE TABLE build_metadata(key TEXT PRIMARY KEY,value TEXT)')
                with store.connection:store.connection.execute('INSERT INTO build_metadata VALUES (?,?)',('dataset_id','fixture'))
            finally:store.close()
            a=build(source,root/'a.json');b=build(source,root/'b.json')
            self.assertEqual(a,b)
            self.assertEqual(sum(row['attempts'] for row in a['pairs'].values()),a['attempts'])
            self.assertEqual(sum(row['batter_runs'] for row in a['pairs'].values()),sum(row['batter_runs'] for row in a['phases'].values()))
            self.assertTrue(all(key.startswith('player:cricsheet:') for key in a['pairs']))
            self.assertIsNone(a['historical_publication_availability'])
            with self.assertRaises(ValueError):build(source,root/'a.json')


if __name__=='__main__':unittest.main()
