"""Separate chronological terminal-score and joint match-result candidates."""
import argparse
from collections import Counter,defaultdict,deque
from datetime import date
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .contextual import discover,split_dates,calibrated
from .baseline import metrics,cluster_interval
from ..pipeline.artifacts import digest
from ..pipeline.events import canonicalize,encoded
from ..pipeline.scoring import NOT_DISMISSED

SCORE_LABELS = ('0','1-9','10-19','20-29','30-49','50-74','75-99','100+')
MATCH_LABELS = ('team_a_win','team_b_win','tie')
FAMILIES = {'player':('global','entry','batter','first_bowler','venue','opposition','recent_form'),
            'match':('global','team_a','team_b','rivalry','venue','team_a_form','team_b_form')}
STRENGTHS = {'player':(0,20,40,80,80,80,10),'match':(0,40,40,30,80,10,10)}


def score_bin(runs):
    return next((i for i,upper in enumerate((0,9,19,29,49,74,99)) if runs<=upper),7)


def extract(raw,source_id):
    """Labels use future sequence; context is captured strictly before first attempt."""
    metadata, events = canonicalize(raw,source_id)
    teams = sorted(metadata['teams'])
    outcome = raw['info']['outcome']
    winner = outcome.get('winner')
    result = teams.index(winner) if winner in teams else 2
    rows, states, seen, dismissed = [], {}, {}, set()
    venue = raw['info']['venue'].strip()
    for event in events:
        innings = event['innings']
        if event['kind']!='delivery' or innings not in (1,2) or metadata['innings'][innings-1]['super_over']:
            continue
        state = states.setdefault(innings,{'legal':0,'wickets':0})
        batter = event['striker']; key = (innings,batter)
        if key not in seen:
            phase = 0 if state['legal']<36 else 1 if state['legal']<90 else 2
            entry = f"{innings}:{phase}:{min(state['wickets']//3,2)}"
            opposition = next(t for t in teams if t!=metadata['innings'][innings-1]['team'])
            seen[key] = {'keys':('all',entry,batter,event['bowler'],venue,opposition),
                         'batter':batter,'runs':0,'not_out':True,'match_id':source_id}
        seen[key]['runs'] += event['runs']['batter']
        for wicket in event['wickets']:
            if wicket['kind'] not in NOT_DISMISSED:
                dismissed.add((innings,wicket['player_id']))
                state['wickets'] += 1
        state['legal'] += int(not(event['extras'].get('wides') or event['extras'].get('noballs')))
    for key,row in seen.items():
        row['not_out'] = key not in dismissed
        row['target'] = score_bin(row.pop('runs'))
        rows.append(row)
    match = {'keys':('all',teams[0],teams[1],'|'.join(teams),venue),'target':result,
             'teams':teams,'match_id':source_id}
    return rows,match


def vectors(model,keys,forms):
    n = len(model['labels'])
    prior = np.asarray(model['counts']['global']['all'],dtype=float)+1
    prior /= prior.sum()
    values, sizes = [prior],[sum(model['counts']['global']['all'])]
    for i,family in enumerate(model['families'][1:],1):
        raw = forms[i-len(keys)] if i>=len(keys) else model['counts'][family].get(keys[i])
        counts = np.zeros(n) if raw is None else np.asarray(raw,dtype=float)
        strength = model['strengths'][i]
        values.append((counts+strength*prior)/(counts.sum()+strength))
        sizes.append(int(counts.sum()))
    return np.asarray(values),sizes


def predict(model,keys,forms):
    array,sizes = vectors(model,keys,forms)
    distribution = calibrated(np.asarray(model['weights'])@array,model['temperature'])
    return distribution,sizes


def fit(directory,output,cutoff):
    from scipy.optimize import minimize_scalar
    from ..paths import PROJECT_ROOT,PACKAGE_ROOT
    output = Path(output).resolve()
    if any(output==p or output.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):
        raise ValueError('Outcome artifacts must remain private')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a fresh outcome artifact directory')
    started = time.perf_counter()
    matches,exclusions = discover(directory,cutoff)
    eligible = []
    for item in matches:
        raw = json.loads(item['path'].read_text(encoding='utf-8'))
        outcome = raw['info'].get('outcome',{})
        regular = [inn for inn in raw['innings'] if not inn.get('super_over')]
        if len(regular)!=2 or not (outcome.get('winner') in raw['info']['teams'] or outcome.get('result')=='tie'):
            exclusions['incomplete_or_no_result'] = exclusions.get('incomplete_or_no_result',0)+1
        else:eligible.append(item)
    matches = eligible
    first,second = split_dates(matches)
    models,samples,histories,deferred = {},{}, {},{}
    for kind,labels in (('player',SCORE_LABELS),('match',MATCH_LABELS)):
        families = FAMILIES[kind]
        base = families[:6] if kind=='player' else families[:5]
        models[kind] = {'schema':'innings-outcomes-v1','kind':kind,'labels':labels,'families':families,
            'strengths':STRENGTHS[kind],'counts':{name:defaultdict(lambda n=len(labels):[0]*n) for name in base},
            'weights':[1/7]*7,'temperature':1,'promoted':False}
        samples[kind] = {'calibration':[],'test':[]}
        histories[kind] = defaultdict(lambda:deque(maxlen=5))
        deferred[kind] = []
    previous,counts,not_out = None,{'player':Counter(),'match':Counter()},Counter()
    def flush():
        for kind in models:
            for key,target in deferred[kind]:histories[kind][key].append(target)
            deferred[kind].clear()
    def form(kind,key):
        values = [0]*len(models[kind]['labels'])
        for target in histories[kind][key]:values[target]+=1
        return values
    for index,item in enumerate(matches):
        if previous!=item['date']:
            flush();previous=item['date']
        raw = json.loads(item['path'].read_text(encoding='utf-8'))
        players,match = extract(raw,item['id'])
        for kind,rows in (('player',players),('match',[match])):
            model,part = models[kind],item['partition']
            for row in rows:
                target = row['target']
                forms = [form(kind,row['batter'])] if kind=='player' else [form(kind,t) for t in row['teams']]
                if kind=='match':forms[1]=[forms[1][1],forms[1][0],forms[1][2]]
                if part=='train':
                    for family,key in zip(model['counts'],row['keys']):model['counts'][family][key][target]+=1
                else:samples[kind][part].append({**row,'forms':forms})
                counts[kind][part]+=1
                if kind=='player':
                    deferred[kind].append((row['batter'],target))
                    not_out[part]+=row['not_out']
                else:
                    a,b = row['teams']
                    deferred[kind].extend(((a,target),(b,1-target if target<2 else 2)))
        if (index+1)%250==0:print(f'Prepared {index+1}/{len(matches)} matches',flush=True)
    flush()
    protocol = digest(PROJECT_ROOT/'docs/INNINGS_OUTCOME_PROTOCOL.md')
    corpus = hashlib.sha256(encoded([(m['id'],m['sha256'],m['partition']) for m in matches]).encode()).hexdigest()
    report = {'protocol_sha256':protocol,'corpus_sha256':corpus,'scope':'male international six-ball T20I',
        'date_range':[matches[0]['date'],matches[-1]['date']],
        'first_dates':{'calibration':first,'test':second},'exclusions':exclusions,
        'matches':dict(Counter(m['partition'] for m in matches)),'player_not_out_rows':dict(not_out),
        'promoted':False,'targets':{},'limitations':'Retrospective new targets on previously examined date cohort; unknown publication times; no prospective, survival or continuation validation.'}
    output.mkdir(parents=True,exist_ok=True)
    for kind,model in models.items():
        rows = samples[kind]['calibration']
        arrays = np.array([vectors(model,r['keys'],r['forms'])[0] for r in rows])
        y = np.array([r['target'] for r in rows])
        actual = arrays[np.arange(len(rows)),:,y]
        weights = np.asarray(model['weights'])
        for _ in range(200):
            responsibilities = actual*weights
            responsibilities /= responsibilities.sum(axis=1,keepdims=True)
            updated = (responsibilities.sum(axis=0)+1)/(len(rows)+7)
            difference = abs(weights-updated).max();weights=updated
            if difference<1e-8:break
        mixture = np.einsum('nfc,f->nc',arrays,weights)
        calibration = minimize_scalar(lambda t:float(-np.log(calibrated(mixture,t)[np.arange(len(y)),y]).mean()),bounds=(.5,3),method='bounded')
        if not calibration.success:raise ValueError('Outcome calibration failed')
        model.update(weights=weights.tolist(),temperature=float(calibration.x))
        rows = samples[kind]['test'];y=np.array([r['target'] for r in rows])
        arrays = np.array([vectors(model,r['keys'],r['forms'])[0] for r in rows])
        predicted = calibrated(np.einsum('nfc,f->nc',arrays,weights),model['temperature'])
        reference = 1 if kind=='player' else 3
        result = {'rows':dict(counts[kind]),'weights':dict(zip(model['families'],model['weights'])),
            'temperature':model['temperature'],'metrics':{name:metrics(rows,y,p) for name,p in
                [('global',arrays[:,0,:]),('entry' if kind=='player' else 'rivalry',arrays[:,reference,:]),('candidate',predicted)]},
            'loss_delta':{name:cluster_interval(rows,y,predicted,p) for name,p in [('global',arrays[:,0,:]),('context_reference',arrays[:,reference,:])]},
            'cold_primary_rows':sum(vectors(model,r['keys'],r['forms'])[1][2 if kind=='player' else 1]==0 for r in rows)}
        if kind=='player':
            result['thresholds']={}
            for threshold,start in ((50,5),(100,7)):
                p = predicted[:,start:].sum(axis=1)
                binary = np.column_stack((1-p,p));truth=(y>=start).astype(int)
                result['thresholds'][str(threshold)] = metrics(rows,truth,binary)
                result['thresholds'][str(threshold)]['observed_positive_rows']=int(truth.sum())
        model.update(protocol_sha256=protocol,corpus_sha256=corpus,data_asof=matches[-1]['date'],
            first_date=matches[0]['date'],training_last_date=max(m['date'] for m in matches if m['partition']=='train'),
            calibration_last_date=max(m['date'] for m in matches if m['partition']=='calibration'),
            recent_forms={key:form(kind,key) for key in histories[kind]})
        path=output/(kind+'-model.json');path.write_text(encoded(model)+'\n',encoding='utf-8')
        result['model_sha256']=digest(path);report['targets'][kind]=result
    report['elapsed_seconds']=round(time.perf_counter()-started,3)
    (output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'matches':len(matches),'rows':counts,'metrics':{k:v['metrics']['candidate']['log_loss'] for k,v in report['targets'].items()}}),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cutoff',default=date.today().isoformat())
    args=parser.parse_args();fit(args.raw_dir,args.output,args.cutoff)


if __name__=='__main__':main()
