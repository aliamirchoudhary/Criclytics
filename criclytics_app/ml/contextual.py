"""Chronological contextual multinomial candidate; no speculative context coefficients."""
import argparse
from collections import Counter, defaultdict, deque
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from ..pipeline.events import canonicalize, encoded
from ..pipeline.features import label
from ..pipeline.artifacts import digest
from ..pipeline.scoring import BOWLER_WICKETS

FAMILIES = ('global', 'phase', 'batter', 'bowler', 'pair', 'venue', 'rivalry', 'batter_form', 'bowler_form')
STRENGTHS = (0, 20, 100, 100, 40, 120, 200, 50, 50)


def discover(directory, cutoff):
    rows, exclusions = [], Counter()
    for path in sorted(Path(directory).glob('*.json')):
        raw = json.loads(path.read_text(encoding='utf-8'))
        info = raw.get('info', {})
        if info.get('gender') != 'male' or info.get('team_type') != 'international' or info.get('match_type') not in ('T20', 'IT20'):
            exclusions['outside_scope'] += 1
            continue
        dates = sorted(set(map(str, info.get('dates', []))))
        if len(dates) != 1:
            exclusions['non_single_date'] += 1
            continue
        if dates[0] > cutoff:
            exclusions['after_cutoff'] += 1
            continue
        if info.get('balls_per_over') != 6:
            exclusions['non_six_ball'] += 1
            continue
        rows.append({'date': dates[0], 'id': path.stem, 'path': path, 'sha256': digest(path)})
    return sorted(rows, key=lambda r:(r['date'], r['id'])), dict(exclusions)


def split_dates(matches):
    dates = sorted({m['date'] for m in matches})
    if len(dates) < 10:
        raise ValueError('At least ten distinct match dates required')
    first, second = dates[int(len(dates)*.6)], dates[int(len(dates)*.8)]
    for item in matches:
        item['partition'] = 'train' if item['date'] < first else 'calibration' if item['date'] < second else 'test'
    return first, second


def keys(batter, bowler, venue, teams, innings, phase):
    return ('all', str(innings)+':'+str(phase), batter, bowler, batter+'|'+bowler,
            venue, '|'.join(sorted(teams)) if len(teams) == 2 else '')


def dense(counter, vocabulary):
    result = np.zeros(len(vocabulary), dtype=float)
    for item, count in counter.items():
        result[vocabulary.get(item, 0)] += count
    return result


def pooled(history):
    result = Counter()
    for _, values in history:
        result.update(values)
    return result


def components(model, row_keys, form):
    prior = np.asarray(model['counts']['global']['all'], dtype=float)+1
    prior /= prior.sum()
    distributions, samples = [prior], [sum(model['counts']['global']['all'])]
    for index, family in enumerate(FAMILIES[1:], 1):
        values = form[index-7] if index >= 7 else model['counts'][family].get(row_keys[index])
        values = np.zeros(len(prior)) if values is None else np.asarray(values, dtype=float)
        total = float(values.sum())
        distributions.append((values+STRENGTHS[index]*prior)/(total+STRENGTHS[index]))
        samples.append(int(total))
    return np.asarray(distributions), samples


def calibrated(probabilities, temperature):
    values = np.power(np.clip(probabilities, 1e-15, 1), 1/temperature)
    return values/values.sum(axis=-1, keepdims=True)


def event_bounds(labels, distribution):
    unknown = float(distribution[0])
    checks = {'six':lambda j:j['batter_runs']==6, 'four':lambda j:j['batter_runs']==4,
              'any_wicket':lambda j:bool(j['dismissals']),
              'bowler_credited_wicket':lambda j:any(w in BOWLER_WICKETS for w in j['dismissals']),
              'legal_delivery':lambda j:j['legal'], 'scoreless_attempt':lambda j:j['total_runs']==0}
    result = {}
    joints = [json.loads(item) for item in labels[1:]]
    for name, check in checks.items():
        lower = sum(float(p) for j,p in zip(joints, distribution[1:]) if check(j))
        result[name] = {'lower':lower, 'upper':min(1, lower+unknown)}
    return result


def fit(directory, output, cutoff, maximum=None):
    from scipy.optimize import minimize_scalar
    from .baseline import metrics, cluster_interval
    from ..paths import PROJECT_ROOT, PACKAGE_ROOT
    output = Path(output).resolve()
    if any(output == p or output.is_relative_to(p) for p in (PACKAGE_ROOT/'static', PROJECT_ROOT/'dist')):
        raise ValueError('Model artifacts must remain private')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a fresh private output')
    matches, exclusions = discover(directory, cutoff)
    if maximum:
        matches = matches[-maximum:]
    first, second = split_dates(matches)
    protocol = PROJECT_ROOT/'docs/CONTEXTUAL_MODEL_PROTOCOL.md'
    model = {'artifact_schema':'contextual-v1', 'promoted':False, 'target_kind':'next_attempt',
             'scope':{'format':'T20I','gender':'male','team_type':'international','balls_per_over':6},
             'protocol_sha256':digest(protocol), 'counts':{name:{} for name in FAMILIES[:7]},
             'players':{}, 'venues':[], 'teams':[], 'forms':{}, 'temperature':1., 'weights':[1/9]*9}
    raw_counts = {name:defaultdict(Counter) for name in FAMILIES[:7]}
    histories = {'batter':defaultdict(lambda:deque(maxlen=5)), 'bowler':defaultdict(lambda:deque(maxlen=5))}
    deferred = {'batter':[], 'bowler':[]}
    previous = None
    samples = {'calibration':[], 'test':[]}
    counts = Counter()
    training_labels = Counter()
    venues, teams = set(), set()
    started = time.perf_counter()
    for index, item in enumerate(matches):
        if previous != item['date']:
            for role in histories:
                for identity, counter in deferred[role]:
                    histories[role][identity].append((previous, counter))
                deferred[role] = []
            previous = item['date']
        raw = json.loads(item['path'].read_text(encoding='utf-8'))
        metadata, events = canonicalize(raw, item['id'])
        venue = raw['info']['venue'].strip()
        venues.add(venue); teams.update(metadata['teams'])
        local = {'batter':defaultdict(Counter), 'bowler':defaultdict(Counter)}
        form = {'batter':{}, 'bowler':{}}
        legal = defaultdict(int)
        for event in events:
            if event['kind'] != 'delivery' or metadata['innings'][event['innings']-1]['super_over']:
                continue
            if event['innings'] not in (1,2):
                continue
            batter, bowler = sys.intern(event['striker']), sys.intern(event['bowler'])
            model['players'].setdefault(batter, event['striker_name'])
            model['players'].setdefault(bowler, event['bowler_name'])
            phase = 0 if legal[event['innings']] < 36 else 1 if legal[event['innings']] < 90 else 2
            context = tuple(map(sys.intern, keys(batter,bowler,venue,metadata['teams'],event['innings'],phase)))
            target = sys.intern(label(event))
            local['batter'][batter][target] += 1
            local['bowler'][bowler][target] += 1
            if item['partition'] == 'train':
                for name, key in zip(FAMILIES[:7], context):
                    raw_counts[name][key][target] += 1
                training_labels[target] += 1
            else:
                for role, identity in (('batter',batter),('bowler',bowler)):
                    if identity not in form[role]:
                        form[role][identity] = pooled(histories[role][identity])
                samples[item['partition']].append((context,target,form['batter'][batter],form['bowler'][bowler],item['id']))
            legal[event['innings']] += int(not(event['extras'].get('wides') or event['extras'].get('noballs')))
            counts[item['partition']] += 1
        for role in histories:
            deferred[role].extend(local[role].items())
        if (index+1)%100 == 0:
            print(f'Prepared {index+1}/{len(matches)} matches', flush=True)
    for role in histories:
        for identity, counter in deferred[role]:
            histories[role][identity].append((previous,counter))
    labels = ['OTHER']+[key for key,n in sorted(training_labels.items(),key=lambda p:(-p[1],p[0])) if n>=3][:63]
    vocabulary = {value:index for index,value in enumerate(labels)}
    model['labels'] = labels
    for name, contexts in raw_counts.items():
        model['counts'][name] = {key:dense(values,vocabulary).astype(int).tolist() for key,values in contexts.items()}
    del raw_counts
    for role in histories:
        model['forms'][role] = {identity:{'last_date':history[-1][0], 'matches':len(history),
            'counts':dense(pooled(history),vocabulary).astype(int).tolist()} for identity,history in histories[role].items() if history}
    model.update(venues=sorted(venues), teams=sorted(teams), data_asof=matches[-1]['date'],
        training_last_date=max(m['date'] for m in matches if m['partition']=='train'),
        calibration_last_date=max(m['date'] for m in matches if m['partition']=='calibration'),
        first_date=matches[0]['date'])
    def matrices(rows):
        vectors = np.empty((len(rows),len(labels)), dtype=float)
        observed = np.empty((len(rows),9), dtype=float)
        y = np.array([vocabulary.get(row[1],0) for row in rows])
        cache = {}
        def convert(value):
            key=id(value)
            if key not in cache: cache[key]=dense(value,vocabulary)
            return cache[key]
        return vectors, observed, y, convert
    rows = samples['calibration']
    mixture, true_probs, y, convert = matrices(rows)
    # Only9observed probabilities per row are needed for convex mixture fitting.
    for index,row in enumerate(rows):
        array,_ = components(model,row[0],[convert(row[2]),convert(row[3])])
        true_probs[index]=array[:,y[index]]
    weights=np.full(9,1/9)
    for _ in range(200):
        responsibilities=true_probs*weights
        responsibilities/=responsibilities.sum(axis=1,keepdims=True)
        updated=(responsibilities.sum(axis=0)+1)/(len(rows)+9)
        if np.max(np.abs(updated-weights))<1e-8:
            weights=updated;break
        weights=updated
    model['weights']=weights.tolist()
    for index,row in enumerate(rows):
        array,_=components(model,row[0],[convert(row[2]),convert(row[3])]);mixture[index]=weights@array
    result=minimize_scalar(lambda t:float(-np.log(calibrated(mixture,t)[np.arange(len(y)),y]).mean()),bounds=(.5,3),method='bounded')
    if not result.success:raise ValueError('Calibration failed')
    model['temperature']=float(result.x)
    del mixture,true_probs,rows,convert
    samples['calibration']=[]
    rows=samples['test']; predicted,_,y,convert=matrices(rows)
    global_p=np.empty_like(predicted);phase_p=np.empty_like(predicted)
    coverage=Counter()
    for index,row in enumerate(rows):
        array,n=components(model,row[0],[convert(row[2]),convert(row[3])])
        predicted[index]=calibrated(weights@array,model['temperature'])
        global_p[index],phase_p[index]=array[0],array[1]
        coverage['cold_batter']+=int(n[2]==0);coverage['cold_bowler']+=int(n[3]==0);coverage['unseen_pair']+=int(n[4]==0)
    records=[{'match_id':r[4]} for r in rows]
    corpus=hashlib.sha256(encoded([(m['id'],m['sha256'],m['partition']) for m in matches]).encode()).hexdigest()
    report={'schema_version':1,'protocol_sha256':model['protocol_sha256'],'corpus_sha256':corpus,
        'scope':model['scope'],'date_range':[matches[0]['date'],matches[-1]['date']],
        'partition_first_dates':{'calibration':first,'test':second},
        'matches':dict(Counter(m['partition'] for m in matches)),'rows':dict(counts),'exclusions':exclusions,
        'metrics':{name:metrics(records,y,p) for name,p in [('global',global_p),('phase',phase_p),('contextual',predicted)]},
        'loss_delta':{name:cluster_interval(records,y,predicted,p) for name,p in [('global',global_p),('phase',phase_p)]},
        'test_cold_coverage':dict(coverage),'unknown_test_labels':int((y==0).sum()),
        'weights':dict(zip(FAMILIES,model['weights'])),'temperature':model['temperature'],
        'elapsed_seconds':round(time.perf_counter()-started,3),'promoted':False,
        'availability':'Historical publication/event times unknown. Recent form advances only after completed dates; this is not prospective live validation.'}
    model['corpus_sha256']=corpus
    output.mkdir(parents=True,exist_ok=True)
    (output/'model.json').write_text(encoded(model)+'\n',encoding='utf-8')
    report['model_sha256']=digest(output/'model.json')
    (output/'evaluation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'matches':len(matches),'rows':dict(counts),'metrics':{k:v['log_loss'] for k,v in report['metrics'].items()},'output':str(output)}),flush=True)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cutoff',default=date.today().isoformat())
    parser.add_argument('--max-matches',type=int)
    args=parser.parse_args()
    fit(args.raw_dir,args.output,args.cutoff,args.max_matches)


if __name__=='__main__':main()
