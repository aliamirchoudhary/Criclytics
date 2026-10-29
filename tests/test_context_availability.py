from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import unittest

from criclytics_app import create_app
from criclytics_app.integrations.context_import import import_records
from criclytics_app.services.context_availability import summarize
from criclytics_app.services.match_context import ContextLedger


MATCH = 'match:manual:authored'
STAMP = '2020-01-01T00:00:00+00:00'
TARGET = MATCH+'#i1/d2'


def record(identity='captain',kind='captaincy',value=None):
    return {'schema_version':1,'record_id':identity,'revision':1,'match_id':MATCH,'kind':kind,
        'source':'authored observation','observer':'fixture author','published_at':STAMP,
        'observed_at':STAMP,'effective_at':STAMP,'scope':'public','rights_basis':'own_observation',
        'rights_reference':'Authored fictional fixture; not a real match',
        'value':value or {'team_id':'team:authored','captain_id':'player:authored:a','change_confirmed':True}}


class ContextAvailabilityTests(unittest.TestCase):
    def test_unknown_conflict_expiry_and_same_attempt_are_not_model_features(self):
        weather = record('weather','weather_observation',{'venue_id':'venue:authored',
            'valid_until':'2020-01-01T01:00:00Z','temperature_c':45})
        competing = deepcopy(weather);competing['record_id']='other';competing['value']['temperature_c']=10
        crowd = record('crowd','crowd_event',{'venue_id':'venue:authored','event_id':TARGET,
            'event_kind':'booing','occurred':True})
        result = summarize([weather,competing,crowd],STAMP,'venue:authored','team:authored',TARGET)
        self.assertEqual(result['families']['weather']['status'],'conflict')
        self.assertIsNone(result['families']['weather']['value'])
        self.assertEqual(result['families']['crowd']['status'],'unknown')
        self.assertTrue(all(not r['model_enabled'] for r in result['families'].values()))
        expired = summarize([weather],'2020-01-01T02:00:00Z','venue:authored','',TARGET)
        self.assertEqual(expired['families']['weather']['status'],'unknown')
        self.assertEqual(result['model_effect'],'none')

    def test_atomic_import_and_local_as_issued_privacy(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder);store=root/'context.sqlite3';source=root/'import.json'
            initial = record();source.write_text(json.dumps([initial]))
            self.assertEqual(import_records(source,store),1)
            conflicting = deepcopy(initial);conflicting['value']['captain_id']='player:authored:b'
            source.write_text(json.dumps([record('new'),conflicting]))
            with self.assertRaises(ValueError):import_records(source,store)
            ledger = ContextLedger(store,read_only=True)
            now = datetime.now(timezone.utc).isoformat()
            self.assertEqual(len(ledger.eligible(MATCH,now)),1)
            self.assertEqual(ledger.eligible(MATCH,STAMP,require_ingested=True),[])
            ledger.close()
            private = record('private');private.update(scope='private',owner_id='private-owner')
            source.write_text(json.dumps([private]));import_records(source,store)
            app = create_app({'TESTING':True,'CONTEXT_LEDGER':store,'LIVE_DIR':folder,
                'PROCESSED_DIR':folder,'LIVE_FETCH_ENABLED':False,'REDIS_URL':''})
            url='/api/v1/context-evidence'
            selectors={'match_id':MATCH,'before_event_id':TARGET,'team_id':'team:authored'}
            with app.test_client() as client:
                response = client.get(url,query_string=selectors)
                rows = response.json['families']['captaincy']['records']
                self.assertEqual([r['record_id'] for r in rows],['captain'])
                self.assertIn('no-store',response.headers['Cache-Control'])
                public = client.get(url,query_string=selectors,environ_overrides={'REMOTE_ADDR':'192.0.2.1'})
                self.assertFalse(public.json['available'])
                self.assertTrue(all(r['status']=='unknown' for r in public.json['families'].values()))
                self.assertEqual(client.get(url,query_string={**selectors,'owner_id':'private-owner'}).status_code,400)
                before = client.get(url,query_string={**selectors,'as_of':STAMP})
                self.assertEqual(before.json['families']['captaincy']['status'],'unknown')
                self.assertEqual(client.get(url,query_string={**selectors,'before_event_id':'other#i1/d2'}).status_code,400)
