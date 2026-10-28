from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from criclytics_app import create_app
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.pipeline.events import initial_state, apply_event, encoded, checksum
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.services.forecasts import ForecastService
from tests.test_baseline import artifact
from tests.test_reconciliation import setup_data, observation, next_context, NOW


def model_files(root):
    model = artifact()
    model.update(dataset_id='fictional', features_sha256='fixture', training_last_date='2017-01-01', calibration_last_date='2018-01-01')
    path = root/'model.json'; path.write_text(encoded(model), encoding='utf-8')
    report = root/'evaluation.json'
    report.write_text(encoded({'model_id': digest(path), 'feature_manifest': {'dataset_id':'fictional',
        'rows_sha256':'fixture', 'partitions': {'train_matches':10,'calibration_matches':2,'test_matches':2}}}), encoding='utf-8')
    return path, report


class ForecastTests(unittest.TestCase):
    def test_shared_features_immutable_idempotent_correction_and_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); now = [NOW]; model, report = model_files(root)
            source = root/'source.sqlite3'; meta, one, _ = setup_data()
            collector = LocalCollector(source, enabled=True, clock=lambda:now[0])
            service = ForecastService(source, root/'ledger.sqlite3', model, digest(model), report, digest(report), clock=lambda:now[0])
            try:
                score = apply_event(initial_state(meta, 1), one)
                collector.ingest(meta, observation(meta,'first',[one],next_context(score,2)))
                first = service.forecast(meta['match_id']); self.assertTrue(first['forecast_allowed'],first)
                issued = deepcopy(first['forecast'])
                self.assertAlmostEqual(sum(issued['content']['distribution'].values()), 1)
                self.assertAlmostEqual(issued['content']['unknown_mass'], .1)
                self.assertEqual(issued['content']['feature_hash'], checksum(first['core']['features']))
                for _ in range(20): self.assertEqual(service.forecast(meta['match_id'])['forecast'], issued)
                self.assertEqual(service.inferences, 1)
                corrected = deepcopy(one); corrected['revision']=2; corrected['runs']['batter']=2;corrected['runs']['total']=2
                now[0] += 1; score = apply_event(initial_state(meta,1), corrected)
                collector.ingest(meta, observation(meta,'changed',[corrected],next_context(score,2,'player:a','player:b')))
                second = service.forecast(meta['match_id'])['forecast']
                self.assertEqual(second['replaces_forecast_id'],issued['forecast_id'])
                self.assertEqual(service.history(meta['match_id'])[-1], issued)
                now[0] += 16
                blocked = service.forecast(meta['match_id']); self.assertIsNone(blocked['forecast']); self.assertIn('next_announcement_expired',blocked['blocked_reasons'])
                self.assertEqual(len(service.history(meta['match_id'])),2)
            finally: collector.close()

    def test_domain_end_missing_hash_and_disabled_api_privacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model,report=model_files(root);source=root/'source.sqlite3';meta,one,_=setup_data()
            meta['format']='ODI'; collector=LocalCollector(source,enabled=True,clock=lambda:NOW)
            try:
                score=apply_event(initial_state(meta,1),one);collector.ingest(meta,observation(meta,'one',[one],next_context(score,2)))
                service=ForecastService(source,root/'ledger.sqlite3',model,digest(model),report,digest(report),clock=lambda:NOW)
                self.assertIn('outside_model_scope',service.forecast(meta['match_id'])['blocked_reasons'])
                with self.assertRaises(ValueError):ForecastService(source,root/'ledger.sqlite3',model,'bad',report,digest(report))
                app=create_app({'TESTING':True,'LIVE_DIR':root/'live','LIVE_FETCH_ENABLED':False,'REDIS_URL':'',
                                'EXPERIMENTAL_FORECASTS':False,'IDENTITY_REGISTRY':'','IDENTITY_PLAYER_STORE':''})
                client=app.test_client();path='/api/v1/workspaces/'+meta['match_id']+'/forecast'
                before_disabled=digest(root/'ledger.sqlite3')
                self.assertEqual(client.get(path).json['blocked_reasons'],['experimental_workspace_disabled'])
                self.assertEqual(digest(root/'ledger.sqlite3'),before_disabled)
                self.assertEqual(service.history(meta['match_id']),[])
                app.extensions['forecast_service']=service
                self.assertEqual(client.get(path).status_code,200)
                self.assertEqual(client.get(path,headers={'Origin':'https://attacker.invalid'}).status_code,403)
                self.assertEqual(client.get(path,headers={'Sec-Fetch-Site':'cross-site'}).status_code,403)
                self.assertEqual(client.get(path,base_url='https://public.invalid').status_code,403)
                self.assertEqual(client.get(path,environ_base={'REMOTE_ADDR':'203.0.113.5'}).status_code,403)
                self.assertIn('no-store',client.get(path).headers['Cache-Control'])
                self.assertEqual(client.get('/api/v1/workspaces/invalid/state').status_code,400)
            finally:collector.close()


if __name__=='__main__':unittest.main()
