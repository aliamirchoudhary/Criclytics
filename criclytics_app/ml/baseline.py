"""Experimental CPU joint-outcome baseline with portable trusted JSON inference."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import platform
import time
import warnings
import numpy as np
from ..pipeline.features import NUMERIC
from ..pipeline.events import encoded
from ..pipeline.artifacts import digest

OTHER='OTHER'


def matrix(rows):
    raw=np.array([[np.nan if row['features'][name] is None else float(row['features'][name]) for name in NUMERIC] for row in rows],dtype=float)
    if np.isinf(raw).any():raise ValueError('Infinite features')
    return np.concatenate((np.nan_to_num(raw,nan=0),np.isnan(raw).astype(float)),axis=1)


def softmax(scores):
    values=np.exp(scores-np.max(scores,axis=1,keepdims=True));return values/values.sum(axis=1,keepdims=True)


def probabilities(artifact,values):
    scaled=(values-np.array(artifact['mean']))/np.array(artifact['scale'])
    known=softmax(scaled@np.array(artifact['coefficients']).T+np.array(artifact['intercepts']))
    result=np.zeros((len(values),len(artifact['labels'])))
    result[:,0]=artifact['unknown_prior']
    result[:,artifact['class_indices']]=known*(1-artifact['unknown_prior'])
    return softmax(np.log(np.clip(result,1e-15,1))/artifact['temperature'])


def validate_artifact(artifact):
    if artifact.get('artifact_schema')!=1 or artifact.get('feature_schema')!=1 or artifact.get('target_kind')!='next_attempt':raise ValueError('Unsupported model contract')
    if artifact.get('feature_names')!=list(NUMERIC) or artifact.get('promoted') is not False:raise ValueError('Unsupported model scope')
    labels=artifact['labels'];width=len(NUMERIC)*2
    if not 3<=len(labels)<=256 or labels[0]!=OTHER or len(set(labels))!=len(labels):raise ValueError('Invalid labels')
    for value in labels[1:]:
        joint=json.loads(value)
        from ..pipeline.scoring import DISMISSALS, NOT_DISMISSED
        if set(joint)!= {'batter_runs','extras','total_runs','dismissals','legal'} or set(joint['extras'])!={'wides','noballs','byes','legbyes','penalty'}:raise ValueError('Invalid joint schema')
        if any(type(n) is not int or n<0 for n in [joint['batter_runs'],joint['total_runs'],*joint['extras'].values()]):raise ValueError('Invalid joint counts')
        if type(joint['legal']) is not bool or not isinstance(joint['dismissals'],list) or any(kind not in DISMISSALS-NOT_DISMISSED for kind in joint['dismissals']):raise ValueError('Invalid joint dismissal/legal status')
        if joint['total_runs']!=joint['batter_runs']+sum(joint['extras'].values()):raise ValueError('Incoherent joint outcome')
        if joint['legal']==bool(joint['extras'].get('wides') or joint['extras'].get('noballs')):raise ValueError('Incoherent legal status')
    for name in ('mean','scale'):
        array=np.asarray(artifact[name],dtype=float)
        if array.shape!=(width,) or not np.isfinite(array).all():raise ValueError('Invalid preprocessing')
    if min(artifact['scale'])<=0:raise ValueError('Invalid scale')
    classes=artifact['class_indices']
    if classes!=list(range(1,len(labels))):raise ValueError('Invalid class mapping')
    if np.asarray(artifact['coefficients']).shape!=(len(classes),width) or np.asarray(artifact['intercepts']).shape!=(len(classes),):raise ValueError('Invalid coefficient dimensions')
    if not np.isfinite(np.asarray(artifact['coefficients'],dtype=float)).all() or not np.isfinite(np.asarray(artifact['intercepts'],dtype=float)).all():raise ValueError('Non-finite weights')
    if not 0<artifact['unknown_prior']<1 or not .5<=artifact['temperature']<=5:raise ValueError('Invalid calibration')
    return artifact


def load_model(path,expected_sha256):
    path=Path(path)
    if not expected_sha256 or path.stat().st_size>2*1024*1024 or digest(path)!=expected_sha256:raise ValueError('Untrusted model artifact')
    return validate_artifact(json.loads(path.read_text(encoding='utf-8')))


def predict(artifact,features):
    if set(features)!=set(NUMERIC):raise ValueError('Feature schema mismatch')
    if any(value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value)) for value in features.values()):raise ValueError('Invalid feature value')
    result=probabilities(artifact,matrix([{'features':features}]))[0]
    if not np.isfinite(result).all() or not np.isclose(result.sum(),1):raise ValueError('Invalid distribution')
    return {label:float(probability) for label,probability in zip(artifact['labels'],result)}


def context(row):return str(int(row['features']['innings']))+':'+str(int(row['features']['phase_band']))


def losses(y,p):
    log=-np.log(np.clip(p[np.arange(len(y)),y],1e-15,1))
    brier=np.square(p).sum(axis=1)-2*p[np.arange(len(y)),y]+1
    return log,brier


def metrics(rows,y,p):
    loss,brier=losses(y,p);confidence=p.max(axis=1);correct=p.argmax(axis=1)==y
    bins=[];ece=0
    for index in range(10):
        mask=(confidence>=index/10)&(confidence<(index+1)/10 if index<9 else confidence<=1)
        n=int(mask.sum())
        if n:
            accuracy=float(correct[mask].mean());mean=float(confidence[mask].mean());ece+=n/len(y)*abs(accuracy-mean)
            bins.append({'lower':index/10,'upper':(index+1)/10,'count':n,'mean_probability':mean,'observed_top_label_fraction':accuracy})
    return {'rows':len(rows),'matches':len({r['match_id'] for r in rows}),'log_loss':float(loss.mean()),
            'multiclass_brier':float(brier.mean()),'top_label_ece_10bins':ece,'reliability':bins}


def cluster_interval(rows,y,p,reference,replicates=200):
    diff=losses(y,p)[0]-losses(y,reference)[0];groups=defaultdict(list)
    for index,row in enumerate(rows):groups[row['match_id']].append(index)
    aggregates=np.array([(diff[ids].sum(),len(ids)) for ids in groups.values()])
    rng=np.random.default_rng(17);values=[]
    for _ in range(replicates):
        sample=aggregates[rng.integers(0,len(aggregates),len(aggregates))]
        values.append(float(sample[:,0].sum()/sample[:,1].sum()))
    return {'method':'whole-match bootstrap','replicates':replicates,'seed':17,'matches':len(groups),
            'loss_delta_vs_reference':float(diff.mean()),'lower_95':float(np.quantile(values,.025)),'upper_95':float(np.quantile(values,.975))}


def read_rows(directory,include):
    rows=[]
    with (Path(directory)/'rows.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line)
            if row['partition'] in include:rows.append(row)
            if len(rows)>50000:raise ValueError('Baseline experiment row budget exceeded')
    return rows


def fit(directory,output,protocol='docs/BASELINE_PROTOCOL.md frozen in d357306; training convergence amendment87bd2c6'):
    from sklearn.linear_model import LogisticRegression
    from sklearn.exceptions import ConvergenceWarning
    from scipy.optimize import minimize_scalar
    from threadpoolctl import threadpool_limits
    import sklearn,scipy
    from tools.measure_repository import working_set
    from ..paths import PACKAGE_ROOT,PROJECT_ROOT
    directory,output=Path(directory),Path(output).resolve()
    if any(output.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Model artifacts must not be public')
    if output.exists():raise ValueError('Use fresh model output; no overwrite')
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['schema_version']!=1 or digest(directory/'rows.jsonl')!=manifest['rows_sha256']:raise ValueError('Feature snapshot mismatch')
    rows=read_rows(directory,{'train','calibration'});train=[r for r in rows if r['partition']=='train'];cal=[r for r in rows if r['partition']=='calibration']
    if len({r['match_id'] for r in train})<5 or len({r['match_id'] for r in cal})<2:raise ValueError('Insufficient match groups')
    labels=[OTHER]+sorted({r['label'] for r in train});mapping={label:i for i,label in enumerate(labels)}
    if len(labels)<3:raise ValueError('Insufficient training outcomes')
    x=matrix(train);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    y=np.array([mapping[r['label']] for r in train]);cal_y=np.array([mapping.get(r['label'],0) for r in cal])
    counts=np.bincount(y,minlength=len(labels))+1;global_prior=counts/counts.sum()
    started=time.perf_counter()
    classifier=LogisticRegression(C=1,solver='lbfgs',max_iter=5000,tol=1e-6,random_state=17)
    with threadpool_limits(limits=1),warnings.catch_warnings():
        warnings.simplefilter('error',ConvergenceWarning);classifier.fit((x-mean)/scale,y)
    coefficients=classifier.coef_;intercepts=classifier.intercept_
    if len(classifier.classes_)==2:
        coefficients=np.vstack((np.zeros_like(coefficients),coefficients));intercepts=np.array([0,intercepts[0]])
    artifact={'artifact_schema':1,'feature_schema':1,'target_kind':'next_attempt','feature_names':list(NUMERIC),'labels':labels,
              'class_indices':classifier.classes_.tolist(),'mean':mean.tolist(),'scale':scale.tolist(),
              'coefficients':coefficients.tolist(),'intercepts':intercepts.tolist(),'unknown_prior':float(global_prior[0]),
              'temperature':1.0,'seed':17,'promoted':False,'training_last_date':manifest['partitions']['train_last_date'],
              'calibration_last_date':manifest['partitions']['calibration_last_date'],'dataset_id':manifest['dataset_id'],
              'features_sha256':manifest['rows_sha256'],'environment':{'python':platform.python_version(),'numpy':np.__version__,'scikit_learn':sklearn.__version__,'scipy':scipy.__version__}}
    cal_matrix=matrix(cal);uncalibrated=probabilities(artifact,cal_matrix)
    if not np.allclose(uncalibrated[:,classifier.classes_]/(1-artifact['unknown_prior']),classifier.predict_proba((cal_matrix-mean)/scale)):raise ValueError('Portable coefficient roundtrip mismatch')
    optimum=minimize_scalar(lambda t:float(losses(cal_y,softmax(np.log(np.clip(uncalibrated,1e-15,1))/t))[0].mean()),bounds=(.5,5),method='bounded',options={'xatol':1e-8})
    if not optimum.success:raise ValueError('Calibration failed')
    artifact['temperature']=float(optimum.x);validate_artifact(artifact)
    output.mkdir(parents=True);model_path=output/'model.json';model_path.write_text(encoded(artifact)+'\n',encoding='utf-8')
    model_hash=digest(model_path)
    # Parameters are now frozen; only now materialize held-out test rows.
    test=read_rows(directory,{'test'});test_y=np.array([mapping.get(r['label'],0) for r in test]);test_x=matrix(test)
    if len({r['match_id'] for r in test})<2:raise ValueError('Insufficient held-out matches')
    fit_seconds=time.perf_counter()-started
    phase_counts=defaultdict(lambda:np.zeros(len(labels)))
    for row,index in zip(train,y):phase_counts[context(row)][index]+=1
    empirical=np.tile(global_prior,(len(test),1))
    phase=np.array([(phase_counts.get(context(r),np.zeros(len(labels)))+20*global_prior)/(phase_counts.get(context(r),np.zeros(len(labels))).sum()+20) for r in test])
    predicted=probabilities(artifact,test_x)
    predictions={'empirical_smoothed':empirical,'phase_innings_smoothed':phase,'logistic_temperature':predicted}
    evaluation={name:metrics(test,test_y,p) for name,p in predictions.items()}
    subgroups={}
    predicates={'actual_dismissal':lambda r:bool(json.loads(r['label'])['dismissals']),
                'actual_illegal':lambda r:not json.loads(r['label'])['legal'],'cold_batter_history':lambda r:r['features']['prior_batter_samples']==0,
                'powerplay_band':lambda r:r['features']['phase_band']==0,'middle_band':lambda r:r['features']['phase_band']==1,
                'death_band':lambda r:r['features']['phase_band']==2,'first_innings':lambda r:r['innings']==1,'later_innings':lambda r:r['innings']>1}
    for name,predicate in predicates.items():
        indices=[i for i,row in enumerate(test) if predicate(row)]
        if indices:subgroups[name]={model:metrics([test[i] for i in indices],test_y[indices],p[indices]) for model,p in predictions.items()}
    trusted=load_model(model_path,model_hash);start=time.perf_counter()
    for _ in range(100):distribution=predict(trusted,test[0]['features'])
    inference_ms=(time.perf_counter()-start)*10
    assert np.allclose(list(distribution.values()),predicted[0])
    report={'model_id':model_hash,'protocol':protocol,'feature_manifest':manifest,
            'test_metrics':evaluation,'subgroups':subgroups,'match_cluster_uncertainty':cluster_interval(test,test_y,predicted,empirical),
            'phase_baseline_uncertainty':cluster_interval(test,test_y,predicted,phase),
            'temperature':artifact['temperature'],'test_unseen_joint_outcomes':int((test_y==0).sum()),'vocabulary_size':len(labels),
            'train_rows':len(train),'calibration_rows':len(cal),'test_rows':len(test),'fit_and_calibration_seconds':fit_seconds,
            'inference_ms_mean_100':inference_ms,'resident_bytes':working_set(),'artifact_bytes':model_path.stat().st_size,
            'promoted':False,'public_predictions_available':False,
            'limitations':['Bounded file-selected historical maleT20I subset; not representative current careers.',
                           'Historical source availability unknown; prospective parity/calibration not established.',
                           'OTHER mass is explicit; wicket/runs marginals cannot treat it as a known physical outcome.',
                           'Rare/subgroup and21match uncertainty are limited; ECE is diagnostic, not proof.']}
    (output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--features',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=fit(args.features,args.output);print(json.dumps({'model_id':result['model_id'],'promoted':False}))


if __name__=='__main__':main()
