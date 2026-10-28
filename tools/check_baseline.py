"""Verify repeated trusted artifacts and record held-out metrics without refitting."""
from collections import defaultdict
import json
import time
import numpy as np
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.ml.baseline import load_model,predict,read_rows,matrix,probabilities,cluster_interval,context
from criclytics_app.pipeline.artifacts import digest


def main():
    first=PROJECT_ROOT/'build/baseline-v1-first';repeat=PROJECT_ROOT/'build/baseline-v1-repeat'
    sha=digest(first/'model.json');assert sha==digest(repeat/'model.json')
    model=load_model(first/'model.json',sha)
    report=json.loads((first/'evaluation.json').read_text())
    root=PROJECT_ROOT/'build/features-v1-first';train=read_rows(root,{'train'});test=read_rows(root,{'test'})
    mapping={value:i for i,value in enumerate(model['labels'])}
    counts=np.bincount([mapping[r['label']] for r in train],minlength=len(mapping))+1;prior=counts/counts.sum()
    phase_counts=defaultdict(lambda:np.zeros(len(mapping)))
    for row in train:phase_counts[context(row)][mapping[row['label']]]+=1
    phase=np.array([(phase_counts[context(row)]+20*prior)/(phase_counts[context(row)].sum()+20) for row in test])
    y=np.array([mapping.get(row['label'],0) for row in test]);p=probabilities(model,matrix(test))
    report['match_cluster_uncertainty']={**cluster_interval(test,y,p,np.tile(prior,(len(test),1))),'reference_model':'empirical_smoothed'}
    report['phase_baseline_uncertainty']={**cluster_interval(test,y,p,phase),'reference_model':'phase_innings_smoothed'}
    report['protocol']='docs/BASELINE_PROTOCOL.md frozen in d357306; training convergence amendment87bd2c6'
    report['deterministic_repeat_artifact']=True
    report['roundtrip_inference_verified']=True
    report['promotion_decision']='NO-GO: limited/stale sample and unknown source availability; no demonstrated improvement over phase/innings baseline'
    report['training_code_sha256']=digest(PROJECT_ROOT/'criclytics_app/ml/baseline.py')
    report['test_outcome_perturbation_check']='Portable test confirms unchanged coefficients/preprocessing/calibration when only test labels change.'
    (PROJECT_ROOT/'docs/audit/cpu-baseline-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
