"""Frozen training-only empirical and phase baselines for future shadow issuance."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from .baseline import load_model, read_rows, context
from ..pipeline.artifacts import digest
from ..services.json_io import atomic_json, read_json
from ..paths import PACKAGE_ROOT, PROJECT_ROOT


def build(features, model_path, expected_model, output):
    output=Path(output).resolve()
    if output.exists() or any(output.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist',PROJECT_ROOT/'data')):
        raise ValueError('Use a fresh private baseline artifact')
    model=load_model(model_path,expected_model);manifest=read_json(Path(features)/'manifest.json')
    if manifest['rows_sha256']!=digest(Path(features)/'rows.jsonl') or manifest['rows_sha256']!=model['features_sha256']:
        raise ValueError('Training export mismatch')
    rows=read_rows(features,{'train'});labels=model['labels'];mapping={label:i for i,label in enumerate(labels)}
    counts=np.ones(len(labels));phases=defaultdict(lambda:np.zeros(len(labels)))
    for row in rows:
        index=mapping[row['label']];counts[index]+=1;phases[context(row)][index]+=1
    result={'schema_version':1,'feature_schema':1,'dataset_id':model['dataset_id'],'model_id':expected_model,
            'features_sha256':model['features_sha256'],'training_last_date':model['training_last_date'],
            'labels':labels,'prior':(counts/counts.sum()).tolist(),'phase_counts':{k:v.tolist() for k,v in sorted(phases.items())},
            'shrinkage':20,'training_rows':len(rows),'promoted':False,
            'protocol_sha256':digest(PROJECT_ROOT/'docs/SHADOW_PROTOCOL.md')}
    atomic_json(output,result);return result


def load(path, expected, model_id, model):
    path=Path(path)
    if not expected or path.stat().st_size>2*1024*1024 or digest(path)!=expected:raise ValueError('Untrusted baseline artifact')
    value=read_json(path)
    if (value.get('schema_version')!=1 or value.get('feature_schema')!=1 or value.get('model_id')!=model_id
            or value.get('labels')!=model['labels'] or value.get('dataset_id')!=model['dataset_id']
            or value.get('features_sha256')!=model['features_sha256'] or value.get('shrinkage')!=20):
        raise ValueError('Baseline contract mismatch')
    prior=np.asarray(value['prior'],dtype=float)
    if prior.shape!=(len(model['labels']),) or not np.isfinite(prior).all() or min(prior)<=0 or not np.isclose(prior.sum(),1):
        raise ValueError('Invalid baseline prior')
    for counts in value['phase_counts'].values():
        array=np.asarray(counts,dtype=float)
        if array.shape!=prior.shape or not np.isfinite(array).all() or min(array)<0:raise ValueError('Invalid phase counts')
    return value


def predict(artifact, features):
    prior=np.asarray(artifact['prior']);key=str(int(features['innings']))+':'+str(int(features['phase_band']))
    counts=np.asarray(artifact['phase_counts'].get(key,[0]*len(prior)))
    phase=(counts+20*prior)/(counts.sum()+20)
    return {name:{label:float(p) for label,p in zip(artifact['labels'],values)}
            for name,values in [('empirical',prior),('phase_innings',phase)]}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('features','model','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--model-sha256',required=True);args=parser.parse_args()
    build(args.features,args.model,args.model_sha256,args.output);print(digest(args.output))
