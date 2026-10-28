from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from criclytics_app.ml.baseline import validate_artifact,load_model,predict,encoded,cluster_interval
from criclytics_app.pipeline.features import NUMERIC
from criclytics_app.pipeline.artifacts import digest


def artifact():
    joint=lambda runs:encoded({'batter_runs':runs,'extras':{k:0 for k in ('wides','noballs','byes','legbyes','penalty')},'total_runs':runs,'dismissals':[],'legal':True})
    width=len(NUMERIC)*2
    return {'artifact_schema':1,'feature_schema':1,'target_kind':'next_attempt','feature_names':list(NUMERIC),'promoted':False,
            'labels':['OTHER',joint(0),joint(1)],'class_indices':[1,2],'mean':[0]*width,'scale':[1]*width,
            'coefficients':[[0]*width]*2,'intercepts':[0,0],'unknown_prior':.1,'temperature':1}


class BaselineTests(unittest.TestCase):
    def test_finite_coherent_roundtrip_and_cold_missing_input(self):
        model=validate_artifact(artifact());features={name:None for name in NUMERIC}
        distribution=predict(model,features)
        self.assertAlmostEqual(sum(distribution.values()),1);self.assertAlmostEqual(distribution['OTHER'],.1)
        self.assertTrue(all(0<=p<=1 for p in distribution.values()))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.json';path.write_text(encoded(model))
            restored=load_model(path,digest(path));self.assertEqual(predict(restored,features),distribution)
            with self.assertRaises(ValueError):load_model(path,'incorrect')
            model['artifact_schema']=2;path.write_text(encoded(model))
            with self.assertRaises(ValueError):load_model(path,digest(path))
        features['runs']=float('nan')
        with self.assertRaises(ValueError):predict(restored,features)

    def test_bad_weights_and_incoherent_joint_outcomes_rejected(self):
        for modify in (lambda m:m['scale'].__setitem__(0,0),lambda m:m['coefficients'][0].__setitem__(0,float('inf')),
                       lambda m:m['labels'].__setitem__(1,m['labels'][1].replace('"total_runs":0','"total_runs":3'))):
            model=artifact();modify(model)
            with self.assertRaises(ValueError):validate_artifact(model)

    def test_uncertainty_groups_whole_matches(self):
        rows=[{'match_id':'a'},{'match_id':'a'},{'match_id':'b'}];y=np.array([0,1,0]);p=np.array([[.7,.3],[.3,.7],[.5,.5]])
        interval=cluster_interval(rows,y,p,p)
        self.assertEqual(interval['matches'],2);self.assertAlmostEqual(interval['upper_95'],0);self.assertAlmostEqual(interval['lower_95'],0)

    def test_test_outcomes_cannot_change_fit_or_preprocessing(self):
        from criclytics_app.ml.baseline import fit
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def dataset(name,changed):
                output=root/name;output.mkdir();rows=[]
                for match in range(9):
                    partition='train' if match<5 else 'calibration' if match<7 else 'test'
                    for attempt in range(10):
                        features={key:None for key in NUMERIC};features.update(innings=1,phase_band=0,prior_batter_samples=0)
                        value=artifact()['labels'][1+attempt%2]
                        if changed and partition=='test':value=artifact()['labels'][1]
                        rows.append({'partition':partition,'match_id':str(match),'features':features,'label':value,'innings':1})
                (output/'rows.jsonl').write_text(''.join(encoded(row)+'\n' for row in rows))
                manifest={'schema_version':1,'rows_sha256':digest(output/'rows.jsonl'),'dataset_id':'fictional',
                          'partitions':{'train_last_date':'2020-01-05','calibration_last_date':'2020-01-07'}}
                (output/'manifest.json').write_text(json.dumps(manifest));return output
            first=dataset('first',False);second=dataset('second',True)
            fit(first,root/'model-a');fit(second,root/'model-b')
            a=json.loads((root/'model-a/model.json').read_text());b=json.loads((root/'model-b/model.json').read_text())
            for key in ('coefficients','intercepts','mean','scale','temperature','labels','unknown_prior'):
                self.assertEqual(a[key],b[key],key)
