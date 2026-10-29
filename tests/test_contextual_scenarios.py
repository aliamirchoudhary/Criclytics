"""Authored chronology/leakage tests and coherent shared scenario probabilities."""
import json
from pathlib import Path
import tempfile
import unittest

from criclytics_app import create_app
from criclytics_app.ml.contextual import fit
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.services.scenarios import ScenarioModel


def corpus(root):
    root.mkdir()
    for index in range(20):
        deliveries=[]
        for runs in (0,1,4,6,0,1):
            deliveries.append({'batter':'A','non_striker':'B','bowler':'X',
                               'runs':{'batter':runs,'extras':0,'total':runs}})
        raw={'meta':{'data_version':'1.1.0','created':'2020-01-01','revision':1},
             'info':{'balls_per_over':6,'dates':[f'2020-01-{index+1:02}'],'gender':'male',
                     'team_type':'international','match_type':'T20','players':{'Team A':['A','B'],'Team X':['X','Y']},
                     'registry':{'people':{'A':'aaaaaaaa','B':'bbbbbbbb','X':'cccccccc','Y':'dddddddd'}},
                     'teams':['Team A','Team X'],'venue':'Authored Ground','outcome':{'winner':'Team A','by':{'runs':1}}},
             'innings':[{'team':'Team A','overs':[{'over':0,'deliveries':deliveries}]}]}
        (root/f'{index:03}.json').write_text(json.dumps(raw),encoding='utf-8')


class ContextualTests(unittest.TestCase):
    def test_test_outcomes_cannot_change_training_vocabulary_or_calibration(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'raw';corpus(raw)
            fit(raw,root/'first','2020-12-31')
            first=json.loads((root/'first/model.json').read_text())
            for path in sorted(raw.glob('*.json'))[-4:]:
                data=json.loads(path.read_text())
                for event in data['innings'][0]['overs'][0]['deliveries']:
                    event['runs']['batter']=event['runs']['total']=5
                path.write_text(json.dumps(data))
            fit(raw,root/'second','2020-12-31')
            second=json.loads((root/'second/model.json').read_text())
            for name in ('labels','counts','weights','temperature','training_last_date','calibration_last_date'):
                self.assertEqual(first[name],second[name],name)
            self.assertNotEqual(first['forms'],second['forms'])
            self.assertTrue(all(json.loads(label)['batter_runs']!=5 for label in second['labels'][1:]))

    def test_hash_scope_temporal_guards_and_probability_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'raw';corpus(raw);output=root/'candidate'
            fit(raw,output,'2020-12-31')
            path,report=output/'model.json',output/'evaluation.json'
            service=ScenarioModel(path,digest(path),report,digest(report))
            result=service.predict('player:cricsheet:aaaaaaaa','player:cricsheet:cccccccc','Authored Ground',
                                   ['Team A','Team X'],as_of='2020-01-20')
            self.assertAlmostEqual(sum(result['distribution'].values()),1)
            self.assertEqual(result['component_samples']['pair'],72)
            self.assertEqual(result['recent_form']['batter']['matches'],5)
            self.assertFalse(result['promoted'])
            for bounds in result['events'].values():
                self.assertGreaterEqual(bounds['lower'],0);self.assertLessEqual(bounds['upper'],1)
                self.assertLessEqual(bounds['lower'],bounds['upper'])
            self.assertLessEqual(result['events']['bowler_credited_wicket']['lower'],result['events']['any_wicket']['lower'])
            with self.assertRaises(ValueError):service.predict('player:cricsheet:aaaaaaaa','player:cricsheet:cccccccc','Authored Ground',as_of='2020-01-19')
            with self.assertRaises(ValueError):service.predict('player:cricsheet:aaaaaaaa','player:cricsheet:aaaaaaaa','Authored Ground')
            with self.assertRaises(ValueError):ScenarioModel(path,'wrong',report,digest(report))
            cold=service.predict('player:cricsheet:11111111','player:cricsheet:22222222','Authored Ground',as_of='2020-01-20')
            self.assertTrue(cold['cold_start']);self.assertEqual(cold['component_samples']['batter'],0)
            app=create_app({'TESTING':True,'LIVE_DIR':root/'live','REDIS_URL':'','LIVE_FETCH_ENABLED':False,
                'IDENTITY_REGISTRY':'','IDENTITY_PLAYER_STORE':'','EXPERIMENTAL_FORECASTS':False,
                'SCENARIO_MODEL':path,'SCENARIO_MODEL_SHA256':digest(path),
                'SCENARIO_EVALUATION':report,'SCENARIO_EVALUATION_SHA256':digest(report)})
            client=app.test_client()
            url='/api/v1/scenarios?batter=player:cricsheet:aaaaaaaa&bowler=player:cricsheet:cccccccc&venue=Authored%20Ground&as_of=2020-01-20'
            self.assertEqual(client.get(url).status_code,200)
            self.assertEqual(client.get(url+'&pressure=booing').status_code,400)
            self.assertEqual(client.get('/build/candidate/model.json').status_code,404)
            self.assertEqual(client.get('/api/v1/scenarios/catalog').json['matches']['test'],4)
            damaged=json.loads(path.read_text());damaged['weights'][0]=float('nan')
            path.write_text(json.dumps(damaged));evaluation=json.loads(report.read_text());evaluation['model_sha256']=digest(path);report.write_text(json.dumps(evaluation))
            with self.assertRaises(ValueError):ScenarioModel(path,digest(path),report,digest(report))
