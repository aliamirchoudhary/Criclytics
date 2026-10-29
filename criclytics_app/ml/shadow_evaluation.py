"""Audit first-issued forecasts against reviewed timing; missing evidence stays missing."""
import argparse
from collections import Counter,defaultdict
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import numpy as np
from .baseline import metrics,cluster_interval,load_model,predict
from .shadow_baselines import load as load_baselines,predict as baseline_predict
from ..pipeline.events import EventStore,checksum,initial_state,apply_event
from ..pipeline.features import History,LocalHistory,vector,label
from ..pipeline.artifacts import digest
from ..services.json_io import read_json
from ..services.weather import utc
from ..paths import PROJECT_ROOT,PACKAGE_ROOT

MODEL='fe917b696bb25d2672b94f68e590fd665cdeed21ec06c55e23bafc1dda319beb'
REGISTERED='2026-10-28T17:31:35Z'


def timing_reasons(issued,event,first,cohort,protocol_sha,baseline_sha):
    reasons=[];content=issued['content'];at=utc(issued['issued_at'])
    if cohort.get('mode')!='manual' or content.get('mode')!='manual':reasons.append('not_prospective_manual')
    review=cohort.get('timing_review',{})
    if not all(isinstance(review.get(key),str) and review[key].strip() for key in ('reviewer','method','evidence_ref')) or cohort.get('rights_confirmed') is not True:
        reasons.append('unreviewed_timing_or_rights')
    if not event.get('event_time') or not first.get('event_time') or not first.get('observed_at'):
        reasons.append('unknown_actual_or_original_observation_time')
    else:
        if event['event_time']!=first['event_time']:reasons.append('actual_start_changed_by_correction')
        if utc(first['event_time'])>utc(first['observed_at']):reasons.append('observation_before_actual_start')
        if at>=utc(first['event_time']) or at>=utc(first['observed_at']):reasons.append('late_or_equal_issue')
    if at<=utc(REGISTERED) or at<utc(cohort['enrolled_at']):reasons.append('before_protocol_or_enrolment')
    if utc(cohort['enrolled_at'])<utc(REGISTERED):reasons.append('enrolment_before_registration')
    if at<utc(content['source_cutoff']):reasons.append('issue_before_source_cutoff')
    if content.get('model_id')!=MODEL or content.get('protocol_sha256')!=protocol_sha:reasons.append('model_or_protocol_mismatch')
    if content.get('baseline_artifact_sha256')!=baseline_sha or set(content.get('baselines',{}))!={'empirical','phase_innings'}:
        reasons.append('missing_or_wrong_preissued_baselines')
    return reasons


def replay_features(store,core):
    """Reassemble the pre-attempt vector from raw receipt/metadata/revision history."""
    cutoff=core['source_cutoff'];mid=core['match_id']
    rows=store.connection.execute("SELECT o.payload FROM observations o JOIN receipts r ON r.hash=o.hash WHERE r.observed_at=? AND json_extract(o.payload,'$.observation_id')=?",
                                  (cutoff,core['source_observation_id'])).fetchall()
    if len(rows)!=1:raise ValueError('Original confirmation receipt is ambiguous/unavailable')
    source=json.loads(rows[0][0]);context=source['next_context']
    if not context or not context['not_started_confirmed'] or source['status']!='in_progress':raise ValueError('Original attempt not confirmed')
    meta=store.metadata(mid,as_of=cutoff);states={i['innings']:initial_state(meta,i['innings']) for i in meta['innings']}
    histories={i:LocalHistory() for i in states};events=list(store.events(mid,as_of=cutoff,allow_unknown=False,include_deleted=True))
    if checksum(events)!=core['source_revision_hash'] or checksum(meta)!=core['metadata_hash']:raise ValueError('Source identity mismatch')
    for event in events:
        if event.get('deleted'):continue
        if event['kind']=='delivery':histories[event['innings']].observe(event)
        apply_event(states[event['innings']],event)
    state=states[context['innings']]
    if any(state[k]!=v for k,v in context['expected_state'].items()):raise ValueError('Original score mismatch')
    # Explicit target/schedule controls are the only model-visible target fields.
    return vector(state,context,History(),histories[context['innings']],meta)


def summarize(rows,labels,prior,counts,lag):
    names=['learner','empirical','phase_innings'];result={name:None for name in names}
    intervals={};subgroups={};drift=None
    if rows:
        mapping={value:i for i,value in enumerate(labels)};y=np.array([mapping.get(row['label'],0) for row in rows])
        arrays={name:np.array([[row[name][label] for label in labels] for row in rows]) for name in names}
        for name in names:result[name]=metrics(rows,y,arrays[name])
        for name in names[1:]:intervals[name]=cluster_interval(rows,y,arrays['learner'],arrays[name])
        groups=defaultdict(list)
        for i,row in enumerate(rows):
            outcome=json.loads(row['label'])
            for group in ('dismissal' if outcome['dismissals'] else 'no_dismissal',
                          'legal' if outcome['legal'] else 'illegal', 'innings_'+str(int(row['features']['innings'])),
                          'phase_'+str(int(row['features']['phase_band'])),
                          'cold' if not row['features']['prior_batter_samples'] else 'observed_history'):
                groups[group].append(i)
        for name,indices in groups.items():subgroups[name]=metrics([rows[i] for i in indices],y[indices],arrays['learner'][indices])
        frequency=np.bincount(y,minlength=len(labels))/len(y)
        drift={'outcome_frequency_l1_from_training_prior':float(np.abs(frequency-prior).sum()),'unseen_outcomes':int((y==0).sum())}
    n=counts['collected_attempts'];scored=len(rows);matches=len({r['match_id'] for r in rows})
    coverage=scored/n if n else None;timed=counts['reviewed_start_times']/n if n else None
    p95=float(np.percentile(lag,95)) if lag else None
    gates={'minimum_matches':matches>=30 and counts['completed_matches']>=30,'minimum_attempts':scored>=5000,'coverage':coverage is not None and coverage>=.9,
           'reviewed_timing':timed is not None and timed>=.95,'source_lag':p95 is not None and p95<=5,
           'beats_both_baselines':len(intervals)==2 and all(v['upper_95']<0 for v in intervals.values()),
           'calibration':result['learner'] is not None and result['learner']['top_label_ece_10bins']<=.03,
           'rare_event_support':all(subgroups.get(key,{}).get('rows',0)>=100 for key in ('dismissal','illegal'))}
    return {'counts':dict(counts),'scored_attempts':scored,'scored_matches':matches,'collected_attempt_coverage':coverage,
            'reviewed_timing_fraction':timed,'source_lag_p95_seconds':p95,'metrics':result,'subgroups':subgroups,
            'learner_minus_baseline_log_loss_intervals':intervals,'drift':drift,'gates':gates,
            'promotion_decision':'REVIEW_REQUIRED' if all(gates.values()) else 'NO-GO',
            'human_release_review_required':True,'external_source_completeness':None,
            'context_ablations':{key:{'enabled':False,'prospective_benefit':None} for key in ('weather','lineup_pitch_home','fielding','media_crowd')}}


def evaluate(source,ledger,cohort,model_path,baseline_path,baseline_sha):
    if Path(cohort).stat().st_size>1024*1024:raise ValueError('Cohort declaration budget exceeded')
    protocol_sha=digest(PROJECT_ROOT/'docs/SHADOW_PROTOCOL.md');cohort=read_json(cohort)
    if cohort.get('schema_version')!=1 or cohort.get('protocol_sha256')!=protocol_sha:raise ValueError('Cohort protocol mismatch')
    members=cohort['matches']
    if len(members)>30 or len({m['match_id'] for m in members})!=len(members):raise ValueError('Cohort size/identity conflict')
    model=load_model(model_path,MODEL);baselines=load_baselines(baseline_path,baseline_sha,MODEL,model)
    if (cohort.get('model_id')!=MODEL or cohort.get('baseline_sha256')!=baseline_sha
            or baselines.get('protocol_sha256')!=protocol_sha or utc(cohort['frozen_artifacts_at'])<utc(REGISTERED)
            or any(utc(m['enrolled_at'])<=utc(cohort['frozen_artifacts_at']) for m in members)):
        raise ValueError('Cohort must bind artifacts frozen before enrolment')
    counts=Counter(collected_attempts=0,completed_matches=0,reviewed_start_times=0,no_issued_forecast=0);rows=[];lag=[]
    if not members:return {'schema_version':1,'protocol_sha256':protocol_sha,'model_id':MODEL,'baseline_sha256':baseline_sha,'cohort_status':'pending_no_enrolled_matches',
                           **summarize([],model['labels'],np.array(baselines['prior']),counts,lag)}
    store=EventStore(source,readonly=True)
    try:
        store.connection.execute('BEGIN')
        with closing(sqlite3.connect(Path(ledger).resolve().as_uri()+'?mode=ro',uri=True)) as db:
            db.execute('BEGIN')
            for member in members:
                mid=member['match_id'];issued={}
                entries=db.execute('SELECT forecast_id,issued_at,payload FROM issued_forecasts WHERE match_id=? ORDER BY rowid LIMIT 10001',(mid,)).fetchall()
                if len(entries)>10000:raise ValueError('Forecast audit budget exceeded')
                for fid,at,payload in entries:
                    entry={'forecast_id':fid,'issued_at':at,'content':json.loads(payload)};target=entry['content']['target_event_id']
                    if target in issued:counts['replacement_forecasts_not_selected']+=1
                    else:issued[target]=entry
                events=list(store.events(mid,include_deleted=True))
                if len(events)>20000:raise ValueError('Event audit budget exceeded')
                metadata=store.metadata(mid)
                first_times=[utc(e['event_time']) for e in events if e['kind']=='delivery' and e.get('event_time')]
                enrolment_late=bool(first_times and utc(member['enrolled_at'])>=min(first_times))
                latest=store.connection.execute("SELECT o.payload FROM observations o JOIN receipts r ON r.hash=o.hash WHERE json_extract(o.payload,'$.match_id')=? ORDER BY r.observed_at DESC LIMIT 1",(mid,)).fetchone()
                if latest and json.loads(latest[0]).get('status')=='completed':counts['completed_matches']+=1
                for event in events:
                    if event['kind']!='delivery' or metadata['innings'][event['innings']-1]['super_over']:continue
                    counts['collected_attempts']+=1
                    if counts['collected_attempts']>100000:raise ValueError('Cohort attempt budget exceeded')
                    first=json.loads(store.connection.execute('SELECT payload FROM events WHERE event_id=? ORDER BY revision LIMIT 1',(event['event_id'],)).fetchone()[0])
                    if not first.get('event_time') or not event.get('event_time'):counts['unknown_actual_start']+=1
                    if not first.get('observed_at'):counts['unknown_original_observation']+=1
                    if first.get('event_time')!=event.get('event_time'):counts['changed_actual_start']+=1
                    review=member.get('timing_review',{})
                    if (event.get('event_time') and first.get('event_time')==event['event_time'] and first.get('observed_at')
                            and all(isinstance(review.get(k),str) and review[k].strip() for k in ('reviewer','method','evidence_ref'))
                            and member.get('rights_confirmed') is True and member.get('mode')=='manual'):
                        counts['reviewed_start_times']+=1
                    if event['revision']>1:counts['corrected_outcomes']+=1
                    if first.get('event_time') and first.get('observed_at'):
                        delay=(utc(first['observed_at'])-utc(first['event_time'])).total_seconds()
                        if delay<0:counts['invalid_negative_source_lag']+=1
                        else:lag.append(delay)
                    entry=issued.pop(event['event_id'],None)
                    if not entry:
                        counts['no_issued_forecast']+=1
                        try:
                            decisions=db.execute('SELECT reasons FROM forecast_decisions WHERE match_id=? AND target_event_id=?',(mid,event['event_id'])).fetchall()
                            for reason in {r for decision in decisions for r in json.loads(decision[0])}:counts['abstention_'+reason]+=1
                        except sqlite3.OperationalError:counts['abstention_detail_unavailable']+=1
                        continue
                    reasons=timing_reasons(entry,event,first,member,protocol_sha,baseline_sha)
                    if enrolment_late:reasons.append('match_enrolled_after_first_attempt')
                    if min(metadata['dates'])<REGISTERED[:10]:reasons.append('match_before_protocol_date')
                    if event.get('deleted'):reasons.append('deleted_outcome')
                    if metadata['format']!='T20I' or metadata['gender']!='male' or metadata['team_type']!='international':reasons.append('outside_cohort_scope')
                    try:
                        content=entry['content'];state=db.execute('SELECT payload FROM state_snapshots WHERE state_id=?',(content['state_id'],)).fetchone()
                        core=json.loads(state[0]);features=replay_features(store,core)
                        if checksum(core)!=content['state_id'] or checksum(features)!=content['feature_hash'] or features!=core['features']:raise ValueError('Feature parity mismatch')
                        expected={'learner':predict(model,features),**baseline_predict(baselines,features)}
                        actual={'learner':content['distribution'],**content['baselines']}
                        for name,values in expected.items():
                            if set(actual[name])!=set(values) or any(abs(actual[name][key]-value)>1e-12 for key,value in values.items()):raise ValueError('Issued probabilities do not reproduce')
                    except (ValueError,KeyError,TypeError,IndexError):reasons.append('state_feature_or_probability_parity_failed')
                    if reasons:
                        for reason in sorted(set(reasons)):counts[reason]+=1
                        continue
                    rows.append({'match_id':mid,'innings':event['innings'],'features':features,'label':label(event),**actual})
                counts['forecasts_without_collected_outcome']+=len(issued)
    finally:store.close()
    return {'schema_version':1,'protocol_sha256':protocol_sha,'model_id':MODEL,'baseline_sha256':baseline_sha,
            'cohort_status':'audited_asserted_timing_requires_human_review',**summarize(rows,model['labels'],np.array(baselines['prior']),counts,lag)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('source','ledger','cohort','model','baselines','output'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--baseline-sha256',required=True);args=parser.parse_args()
    result=evaluate(args.source,args.ledger,args.cohort,args.model,args.baselines,args.baseline_sha256)
    output=args.output.resolve()
    if output.exists() or any(output.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist',PROJECT_ROOT/'data')):
        raise ValueError('Use a fresh private report output')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
