"""Version1 shared before-attempt features, coherent labels and date-grouped partitions."""
import argparse
from collections import defaultdict,deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from .events import EventStore,initial_state,apply_event,encoded
from .scoring import NOT_DISMISSED

SCHEMA_VERSION=1
NUMERIC=('innings','super_over','runs','wickets','legal_balls','attempts','run_rate','partnership_runs','phase_band',
         'recent_six_runs','recent_six_wickets','batter_match_runs','batter_match_balls','bowler_match_legal_balls',
         'prior_batter_samples','prior_matchup_samples','prior_batter_runs_per_attempt','prior_bowler_wicket_rate',
         'prior_matchup_wicket_rate','target','runs_required','balls_remaining')


def outcome(event):
    if event['kind']!='delivery':raise ValueError('Outcome requires a delivery attempt')
    extras=event['extras']
    dismissed=tuple(sorted(w['kind'] for w in event.get('wickets',[]) if w['kind'] not in NOT_DISMISSED))
    return {'batter_runs':event['runs']['batter'],'extras':{name:extras.get(name,0) for name in ('wides','noballs','byes','legbyes','penalty')},
            'total_runs':event['runs']['total'],'dismissals':list(dismissed),'legal':not bool(extras.get('wides') or extras.get('noballs'))}


def label(event):return encoded(outcome(event))


class History:
    def __init__(self):
        self.global_count=self.global_runs=self.global_wickets=0
        self.batters=defaultdict(lambda:[0,0,0]);self.bowlers=defaultdict(lambda:[0,0,0]);self.matchups=defaultdict(lambda:[0,0,0])
        self.last_completed_date=None

    def observe(self,event):
        result=outcome(event);runs=result['total_runs'];wickets=len(result['dismissals'])
        self.global_count+=1;self.global_runs+=result['batter_runs'];self.global_wickets+=int(wickets>0)
        for row in (self.batters[event['striker']],self.bowlers[event['bowler']],self.matchups[(event['striker'],event['bowler'])]):
            row[0]+=1;row[1]+=result['batter_runs'];row[2]+=int(wickets>0)

    def merge(self,other,completed_date):
        self.global_count+=other.global_count;self.global_runs+=other.global_runs;self.global_wickets+=other.global_wickets
        for name in ('batters','bowlers','matchups'):
            target=getattr(self,name)
            for key,values in getattr(other,name).items():
                for index in range(3):target[key][index]+=values[index]
        self.last_completed_date=max(self.last_completed_date or completed_date,completed_date)


class LocalHistory:
    def __init__(self):
        self.recent=deque(maxlen=6);self.batters=defaultdict(lambda:[0,0]);self.bowlers=defaultdict(int)

    def observe(self,event):
        result=outcome(event);self.recent.append((result['total_runs'],len(result['dismissals'])))
        self.batters[event['striker']][0]+=result['batter_runs']
        self.batters[event['striker']][1]+=int(not event['extras'].get('wides'))
        self.bowlers[event['bowler']]+=int(result['legal'])


def vector(state,participants,history,local,metadata):
    # participants is an announced pre-attempt context, never the outcome payload.
    striker,bowler=participants['striker'],participants['bowler']
    batter=history.batters.get(striker,[0,0,0]);bowl=history.bowlers.get(bowler,[0,0,0]);pair=history.matchups.get((striker,bowler),[0,0,0])
    prior_runs=history.global_runs/history.global_count if history.global_count else None
    prior_wicket=history.global_wickets/history.global_count if history.global_count else None
    def smooth(row,column,prior,weight=20):return (row[column]+weight*prior)/(row[0]+weight) if prior is not None else None
    target=state['target'] if state['target_verified'] else None
    info=metadata['innings'][state['innings']-1]
    # A final/reduced historical over limit has unknown availability; do not use it.
    values={'innings':state['innings'],'super_over':int(state['super_over']),'runs':state['runs'],'wickets':state['wickets'],
            'legal_balls':state['legal_balls'],'attempts':state['attempts'],
            'run_rate':state['runs']*metadata['balls_per_over']/state['legal_balls'] if state['legal_balls'] else None,
            'partnership_runs':state['partnership_runs'],'phase_band':0 if state['legal_balls']<36 else 1 if state['legal_balls']<90 else 2,
            'recent_six_runs':sum(r for r,w in local.recent),'recent_six_wickets':sum(w for r,w in local.recent),
            'batter_match_runs':local.batters.get(striker,[0,0])[0],'batter_match_balls':local.batters.get(striker,[0,0])[1],
            'bowler_match_legal_balls':local.bowlers.get(bowler,0),'prior_batter_samples':batter[0],'prior_matchup_samples':pair[0],
            'prior_batter_runs_per_attempt':smooth(batter,1,prior_runs),'prior_bowler_wicket_rate':smooth(bowl,2,prior_wicket),
            'prior_matchup_wicket_rate':smooth(pair,2,prior_wicket),'target':target,
            'runs_required':max(0,target-state['runs']) if target is not None else None,
            'balls_remaining':max(0,state['scheduled_balls']-state['legal_balls']) if state.get('scheduled_balls_verified') else max(0,info['scheduled_balls']-state['legal_balls']) if info.get('scheduled_balls_verified') else None}
    return {key:values[key] for key in NUMERIC}


def partitions(metadata,train_fraction=.6,calibration_fraction=.2):
    if not 0<train_fraction<1 or not 0<calibration_fraction<1 or train_fraction+calibration_fraction>=1:raise ValueError("Invalid split fractions")
    groups=defaultdict(list)
    for item in metadata:groups[item['dates'][0]].append(item['match_id'])
    days=sorted(groups)
    if len(days)<5:raise ValueError('At least five distinct match start dates required')
    train_end=max(1,int(len(days)*train_fraction));cal_end=max(train_end+1,int(len(days)*(train_fraction+calibration_fraction)))
    if cal_end>=len(days):raise ValueError('Insufficient independent test dates')
    train_last=max(d for item in metadata if item['dates'][0] in days[:train_end] for d in item['dates'])
    calibration_first=days[train_end];calibration_last=max(d for item in metadata if item['dates'][0] in days[train_end:cal_end] for d in item['dates'])
    test_first=days[cal_end]
    # Multi-day overlap cannot leak across partitions; require an explicit embargo.
    if train_last>=calibration_first or calibration_last>=test_first:raise ValueError('Chronological partitions overlap; embargo required')
    assignments={mid:('train' if i<train_end else 'calibration' if i<cal_end else 'test') for i,day in enumerate(days) for mid in groups[day]}
    return assignments,{'train_last_date':train_last,'calibration_first_date':calibration_first,'calibration_last_date':calibration_last,'test_first_date':test_first,
                        'matches':{split:sum(v==split for v in assignments.values()) for split in ('train','calibration','test')},
                        'same_day_groups':True,'multi_day_overlap':'rejected_without_embargo'}


def generate(store):
    metadata=[store.metadata(row[0]) for row in store.connection.execute('SELECT match_id FROM matches ORDER BY match_id')]
    metadata=[m for m in metadata if m['format']=='T20I' and m['gender']=='male' and m['team_type']=='international']
    assignments,split_info=partitions(metadata)
    history=History();pending=[]
    for match in sorted(metadata,key=lambda m:(m['dates'][0],m['match_id'])):
        start=match['dates'][0]
        ready=[item for item in pending if item[0]<start];pending=[item for item in pending if item[0]>=start]
        for end,summary in ready:history.merge(summary,end)
        if history.last_completed_date and history.last_completed_date>=start:raise ValueError('Future match history contamination')
        summary=History();states={};locals={}
        for event in store.events(match['match_id']):
            innings=event['innings'];state=states.setdefault(innings,initial_state(match,innings));local=locals.setdefault(innings,LocalHistory())
            if event['kind']=='delivery':
                context={name:event[name] for name in ('striker','non_striker','bowler')}
                features=vector(state,context,history,local,match)
                row={'schema_version':SCHEMA_VERSION,'target_kind':'next_attempt','match_id':match['match_id'],'match_start_date':start,
                     'match_end_date':match['dates'][-1],'event_id':event['event_id'],'innings':innings,'attempt':event['attempt'],
                     'partition':assignments[match['match_id']],'features':features,'label':label(event),
                     'participants':context,'history_cutoff_date':history.last_completed_date,
                     'observed_at':event.get('observed_at'),'historical_availability':'unknown' if event.get('observed_at') is None else 'observed'}
                yield row,split_info
                # Update only after yielding the vector and target.
                local.observe(event);summary.observe(event)
            apply_event(state,event)
        pending.append((match['dates'][-1],summary))


def export(store_path,output):
    from ..paths import PACKAGE_ROOT,PROJECT_ROOT
    output=Path(output).resolve()
    if any(output.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Feature export must not be public')
    if output.exists():raise ValueError('Use a fresh feature export directory')
    output.mkdir(parents=True);store=EventStore(store_path)
    counts=defaultdict(int);fingerprint=hashlib.sha256();split_info=None;rows=0
    try:
        store.connection.execute('BEGIN')
        source_snapshot=hashlib.sha256()
        for table,order in (('matches','match_id'),('events','event_id,revision')):
            for source in store.connection.execute('SELECT payload FROM '+table+' ORDER BY '+order):source_snapshot.update((source[0]+'\n').encode())
        with (output/'rows.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
            for row,split_info in generate(store):
                text=encoded(row)+'\n';stream.write(text);fingerprint.update(text.encode());counts[row['partition']]+=1;rows+=1
        dataset=store.connection.execute("SELECT value FROM build_metadata WHERE key='dataset_id'").fetchone()
        report={'schema_version':SCHEMA_VERSION,'target_kind':'next_attempt','feature_names':list(NUMERIC),
                'rows':rows,'partition_rows':dict(counts),'partitions':split_info,'rows_sha256':fingerprint.hexdigest(),
                'dataset_id':dataset[0] if dataset else None,'source_snapshot_sha256':source_snapshot.hexdigest(),
                'attribution':'Derived from Cricsheet JSON match data (ODC-BY-1.0).',
                'availability_limit':'Historical publication/event times unknown; retrospective chronology is not prospective source-availability proof.'}
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        return report
    finally:store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--store',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.store,args.output),indent=2))


if __name__=='__main__':main()
