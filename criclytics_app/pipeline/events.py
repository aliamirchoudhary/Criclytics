"""Version1 canonical delivery attempts and immutable source observations, SQLite local only."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from .schema import validate_match,normalize_legacy_match
from .scoring import DISMISSALS,NOT_DISMISSED,score_innings
from .artifacts import validate,digest
from .identities import local_id


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)


def checksum(value):return hashlib.sha256(encoded(value).encode()).hexdigest()


def participant(info,name,match_id):
    source=info.get('registry',{}).get('people',{}).get(name)
    return 'player:cricsheet:'+source if source else local_id('player',match_id,name)


def canonicalize(raw,source_id,observed_at=None):
    match=deepcopy(raw);normalize_legacy_match(match);validate_match(match)
    info=match['info'];mid='match:cricsheet:'+str(source_id);source_hash=checksum(raw)
    metadata={'schema_version':1,'match_id':mid,'source_id':str(source_id),'source_hash':source_hash,
              'dates':sorted(str(d) for d in info['dates']),'format':'T20I' if info['match_type'] in ('T20','IT20') else info['match_type'],
              'gender':info['gender'],'team_type':info['team_type'],'balls_per_over':info['balls_per_over'],
              'teams':info['teams'],'innings':[],'event_time_precision':'unknown','observed_at':observed_at}
    events=[]
    for index,innings in enumerate(match['innings'],1):
        imeta={'innings':index,'team':innings['team'],'team_id':local_id('team',info['gender'],info['team_type'],innings['team']),
               'super_over':bool(innings.get('super_over')),'source_target':innings.get('target'),
               'target_availability':'unknown','declared':bool(innings.get('declared')),'forfeited':bool(innings.get('forfeited'))}
        metadata['innings'].append(imeta)
        attempt=0
        def control(kind,runs,attempt_number,order):
            return {'schema_version':1,'match_id':mid,'innings':index,'attempt':attempt_number,'kind':kind,'runs':runs,
                    'event_id':mid+'#i'+str(index)+'/'+kind,'revision':1,'order':order,'source_hash':source_hash,
                    'event_time':None,'observed_at':observed_at,'deleted':False}
        if innings.get('penalty_runs',{}).get('pre'):events.append(control('penalty_pre',innings['penalty_runs']['pre'],0,0))
        for over in innings['overs']:
            legal_in_over=0
            expected=int(innings.get('miscounted_overs',{}).get(str(over['over']),{}).get('balls',info['balls_per_over']))
            for delivery in over['deliveries']:
                attempt+=1;extras=delivery.get('extras',{});legal=not extras.get('wides') and not extras.get('noballs')
                legal_in_over+=int(legal)
                event={'schema_version':1,'match_id':mid,'innings':index,'attempt':attempt,'kind':'delivery',
                       'event_id':mid+'#i'+str(index)+'/d'+str(attempt),'revision':1,'order':attempt*10,
                       'over':over['over'],'over_legal_limit':expected,'over_end':bool(legal and legal_in_over==expected),
                       'striker':participant(info,delivery['batter'],source_id),'non_striker':participant(info,delivery['non_striker'],source_id),
                       'bowler':participant(info,delivery['bowler'],source_id),'striker_name':delivery['batter'],
                       'non_striker_name':delivery['non_striker'],'bowler_name':delivery['bowler'],
                       'runs':deepcopy(delivery['runs']),'extras':deepcopy(extras),
                       'wickets':[{**w,'player_id':participant(info,w['player_out'],source_id)} for w in delivery.get('wickets',[])],
                       'source_hash':source_hash,'event_time':None,'observed_at':observed_at,'deleted':False}
                events.append(event)
        if innings.get('penalty_runs',{}).get('post'):events.append(control('penalty_post',innings['penalty_runs']['post'],attempt+1,(attempt+1)*10+1))
        totals=score_innings(innings,index-1,info['balls_per_over'],metadata['format'])
        closing=control('innings_end',totals['total'],attempt+1,(attempt+1)*10+2)
        closing.update(wickets=totals['wickets'],legal_balls=totals['legal_balls'],completion_reason='source_innings_complete')
        events.append(closing)
    return metadata,events


def validate_event(event):
    if event.get('schema_version')!=1 or not isinstance(event.get('revision'),int) or event['revision']<1:raise ValueError('Invalid event version')
    for name in ('event_id','match_id','source_hash'):
        if not isinstance(event.get(name),str) or not 1<=len(event[name])<=300:raise ValueError('Invalid event identity')
    for name in ('innings','attempt','order'):
        if type(event.get(name)) is not int or event[name]<0:raise ValueError('Invalid event sequence')
    if event['innings']<1:raise ValueError('Invalid innings')
    for name in ('event_time','observed_at'):
        if event.get(name) is not None:
            from datetime import datetime
            value=datetime.fromisoformat(event[name].replace('Z','+00:00'))
            if value.tzinfo is None:raise ValueError('Event timestamps require timezone')
    if event.get('deleted'):return
    kind=event.get('kind')
    if kind=='delivery':
        if event['attempt']<1:raise ValueError('Delivery attempt must be positive')
        if set(event.get('extras',{})) - {'wides','noballs','byes','legbyes','penalty'}:raise ValueError('Unknown extras')
        runs=event['runs'];extras=event['extras']
        if any(type(n) is not int or n<0 for n in [runs.get('batter'),runs.get('total'),runs.get('extras'),*extras.values()]):raise ValueError('Invalid runs')
        if runs['extras']!=sum(extras.values()) or runs['total']!=runs['batter']+runs['extras']:raise ValueError('Run conservation failure')
        if extras.get('wides') and extras.get('noballs'):raise ValueError('Conflicting illegal-ball extras')
        if any(not isinstance(event.get(name),str) or not 1<=len(event[name])<=200 for name in ('striker','non_striker','bowler')):raise ValueError('Missing participant')
        if len({event[name] for name in ('striker','non_striker','bowler')})!=3:raise ValueError('Contradictory participant identities')
        for wicket in event.get('wickets',[]):
            if wicket['kind'] not in DISMISSALS or not wicket.get('player_id'):raise ValueError('Invalid dismissal')
    elif kind in ('penalty_pre','penalty_post','target_revision','schedule_revision','innings_end'):
        if type(event.get('runs')) is not int or event['runs']<0:raise ValueError('Invalid control value')
        if kind in ('target_revision','schedule_revision') and event['runs']<1:raise ValueError('Positive target/schedule required')
        if kind=='innings_end' and any(type(event.get(key)) is not int or event[key]<0 for key in ('wickets','legal_balls')):raise ValueError('Explicit innings closing score required')
        if kind in ('target_revision','schedule_revision') and event.get('observed_at') is None:raise ValueError('Target revisions require observed availability')
    else:raise ValueError('Unsupported event kind')


class EventStore:
    def __init__(self,path,readonly=False):
        from ..paths import PACKAGE_ROOT,PROJECT_ROOT
        self.path=Path(path).resolve()
        if any(self.path.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Event store must not be public')
        if readonly:
            self.connection=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,timeout=2)
            return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.connection=sqlite3.connect(self.path,timeout=10)
        self.connection.executescript("""
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS observations (hash TEXT PRIMARY KEY,source TEXT NOT NULL,payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS receipts (hash TEXT NOT NULL,observed_at TEXT NOT NULL,ingested_at TEXT NOT NULL,PRIMARY KEY(hash,observed_at));
          CREATE TABLE IF NOT EXISTS matches (match_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events (event_id TEXT NOT NULL,revision INTEGER NOT NULL,match_id TEXT NOT NULL,
            innings INTEGER NOT NULL,event_order INTEGER NOT NULL,available_at REAL,observation_hash TEXT NOT NULL,payload TEXT NOT NULL,
            PRIMARY KEY(event_id,revision));
          CREATE TABLE IF NOT EXISTS metadata_revisions (match_id TEXT NOT NULL,revision INTEGER NOT NULL,available_at REAL NOT NULL,payload TEXT NOT NULL,observation_hash TEXT NOT NULL,PRIMARY KEY(match_id,revision));
          CREATE INDEX IF NOT EXISTS ordered_events ON events(match_id,innings,event_order);
        """)

    def close(self):self.connection.close()

    def ingest(self,observation,metadata,events,source='cricsheet',observed_at=None):
        observation_hash=checksum(observation);events=list(events)
        if len(events)>20000:raise ValueError('Observation exceeds event batch bound')
        for event in events:
            validate_event(event)
            if event['innings']>len(metadata['innings']):raise ValueError('Unknown innings')
            if event['match_id']!=metadata['match_id']:raise ValueError('Mixed match batch')
            if event['source_hash']!=observation_hash:raise ValueError('Event observation hash mismatch')
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?)',(observation_hash,source,encoded(observation)))
            self.connection.execute('INSERT OR IGNORE INTO receipts VALUES (?,?,?)',(observation_hash,observed_at or 'unknown',datetime.now(timezone.utc).isoformat()))
            previous=self.metadata(metadata['match_id'])
            if previous and encoded(previous)!=encoded(metadata):raise ValueError('Match metadata revision requires explicit reconciliation')
            self.connection.execute('INSERT OR IGNORE INTO matches VALUES (?,?)',(metadata['match_id'],encoded(metadata)))
            for event in events:
                payload=encoded(event)
                old=self.connection.execute('SELECT payload FROM events WHERE event_id=? AND revision=?',(event['event_id'],event['revision'])).fetchone()
                if old:
                    previous_event=json.loads(old[0])
                    semantic=lambda value:{key:item for key,item in value.items() if key not in ('source_hash','observed_at')}
                    if semantic(previous_event)!=semantic(event):raise ValueError('Conflicting immutable event revision')
                    continue
                available=datetime.fromisoformat(event['observed_at'].replace('Z','+00:00')).timestamp() if event.get('observed_at') else None
                self.connection.execute('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?)',(event['event_id'],event['revision'],event['match_id'],event['innings'],event['order'],available,observation_hash,payload))

    def metadata(self,match_id,as_of=None):
        exists=self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='metadata_revisions'").fetchone()
        if exists:
            from ..services.weather import utc
            cutoff=utc(as_of).timestamp() if as_of else float('inf')
            row=self.connection.execute('SELECT payload FROM metadata_revisions WHERE match_id=? AND available_at<=? ORDER BY revision DESC LIMIT 1',(match_id,cutoff)).fetchone()
            if row:return json.loads(row[0])
        row=self.connection.execute('SELECT payload FROM matches WHERE match_id=?',(match_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def register_metadata(self,metadata,revision,observed_at,source='manual'):
        from ..services.weather import utc
        if type(revision) is not int or revision<2:raise ValueError('Explicit metadata revision2+ required')
        current=self.metadata(metadata['match_id'])
        if current is None:raise ValueError('Base metadata must be observed first')
        value=encoded(metadata)
        old=self.connection.execute('SELECT payload FROM metadata_revisions WHERE match_id=? AND revision=?',(metadata['match_id'],revision)).fetchone()
        if old:
            if old[0]!=value:raise ValueError('Conflicting immutable metadata revision')
            return
        last=self.connection.execute('SELECT MAX(revision) FROM metadata_revisions WHERE match_id=?',(metadata['match_id'],)).fetchone()[0] or 1
        if revision!=last+1:raise ValueError('Metadata revision gap')
        if {k:v for k,v in metadata.items() if k!='innings'}!={k:v for k,v in current.items() if k!='innings'}:raise ValueError('Only explicit appended innings are supported; other identity/rule changes require review')
        if metadata['innings'][:len(current['innings'])]!=current['innings'] or len(metadata['innings'])<=len(current['innings']):raise ValueError('Prior innings metadata is immutable')
        for index,innings in enumerate(metadata['innings'],1):
            if innings['innings']!=index or innings['team_id'] not in {i['team_id'] for i in current['innings']}:raise ValueError('Invalid appended innings identity')
        observation={'metadata':metadata,'revision':revision,'observed_at':observed_at};source_hash=checksum(observation)
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO observations VALUES (?,?,?)',(source_hash,source,encoded(observation)))
            self.connection.execute('INSERT OR IGNORE INTO receipts VALUES (?,?,?)',(source_hash,observed_at,datetime.now(timezone.utc).isoformat()))
            self.connection.execute('INSERT INTO metadata_revisions VALUES (?,?,?,?,?)',(metadata['match_id'],revision,utc(observed_at).timestamp(),value,source_hash))

    def events(self,match_id,as_of=None,allow_unknown=True,include_deleted=False):
        cutoff=datetime.fromisoformat(as_of.replace('Z','+00:00')).timestamp() if as_of else None
        if as_of and datetime.fromisoformat(as_of.replace('Z','+00:00')).tzinfo is None:raise ValueError('Cutoff requires timezone')
        eligible="(available_at IS NULL OR available_at<=?)" if allow_unknown else "(available_at IS NOT NULL AND available_at<=?)"
        if cutoff is None:cutoff=float('inf')
        cursor=self.connection.execute("SELECT e.payload FROM events e WHERE e.match_id=? AND e.revision=(SELECT MAX(revision) FROM events r WHERE r.event_id=e.event_id AND "+eligible+") ORDER BY e.innings,e.event_order,e.event_id",(match_id,cutoff))
        for row in cursor:
            event=json.loads(row[0])
            if include_deleted or not event.get('deleted'):yield event


def initial_state(metadata,innings):
    info=metadata['innings'][innings-1]
    return {'match_id':metadata['match_id'],'innings':innings,'team_id':info['team_id'],'super_over':info['super_over'],
            'runs':0,'wickets':0,'legal_balls':0,'attempts':0,'striker':None,'non_striker':None,'bowler':None,
            'target':None,'target_verified':False,'target_basis':'unavailable','partnership_runs':0,
            'striker_after':None,'non_striker_after':None,'last_revision':None,'legal_ball_id':None,'last_attempt_id':None,'innings_complete':False,'closing_total_match':None,'scheduled_balls':None,'scheduled_balls_verified':False}


def apply_event(state,event):
    if event['kind']=='innings_end':
        state['closing_total_match']=all(state[key]==event[key] for key in ('runs','wickets','legal_balls'))
        state['innings_complete']=state['closing_total_match'];return state
    if event['kind']=='schedule_revision':
        state.update(scheduled_balls=event['runs'],scheduled_balls_verified=True);return state
    if event['kind']=='target_revision':
        state.update(target=event['runs'],target_verified=True,target_basis='explicit_observed_revision');return state
    if event['kind'].startswith('penalty_'):
        state['runs']+=event['runs'];return state
    extras=event['extras'];legal=not extras.get('wides') and not extras.get('noballs')
    state.update(striker=event['striker'],non_striker=event['non_striker'],bowler=event['bowler'])
    state['legal_ball_id']=state['match_id']+'#i'+str(state['innings'])+'/l'+str(state['legal_balls']+1)
    state['last_attempt_id']=event['event_id']
    state['runs']+=event['runs']['total'];state['legal_balls']+=int(legal);state['attempts']+=1
    state['partnership_runs']+=event['runs']['total']
    dismissed=[w for w in event.get('wickets',[]) if w['kind'] not in NOT_DISMISSED]
    state['wickets']+=len(dismissed)
    crossed=event['runs']['batter']+extras.get('byes',0)+extras.get('legbyes',0)+max(0,extras.get('wides',0)-1)
    after=[event['striker'],event['non_striker']]
    if crossed%2:after.reverse()
    if event.get('over_end') and legal:after.reverse()
    # Crossings/replacement batter and old/new caught laws cannot be reconstructed
    # exactly from total runs alone. The next source delivery supplies actual ends.
    if event.get('wickets') or extras.get('noballs',0)>1:after=[None,None]
    if dismissed:state['partnership_runs']=0
    state.update(striker_after=after[0],non_striker_after=after[1],last_revision=event['revision'])
    return state


def replay(metadata,events):
    states={};previous_regular=None
    for event in events:
        innings=event['innings']
        if innings not in states:
            states[innings]=initial_state(metadata,innings)
            info=metadata['innings'][innings-1]
            if previous_regular and not info['super_over'] and metadata['format']!='Test':
                states[innings].update(target=previous_regular['runs']+1,target_basis='derived_prior_innings_unverified')
        apply_event(states[innings],event)
        if not states[innings]['super_over']:previous_regular=states[innings]
    for info in metadata['innings']:
        if info['innings'] not in states:states[info['innings']]=initial_state(metadata,info['innings'])
    return [states[k] for k in sorted(states)]


def import_subset(raw,dataset,output,limit=100,fmt='T20I',start_date=None,end_date=None):
    if not 1<=limit<=500:raise ValueError('Bounded import limit must be1..500')
    if Path(output).exists():raise ValueError('Use fresh event store; never overwrite existing observations')
    manifest=validate(dataset);store=EventStore(output);count=attempts=0
    rejected={row['path'] for row in json.loads((Path(dataset)/'difference_report.json').read_text())['rejected']}
    try:
        for row in manifest['inputs']:
            if row['path'] in rejected:continue
            if fmt=='T20I' and not row['path'].startswith('t20s_male_json/'):continue
            path=(Path(raw)/row['path']).resolve()
            if not path.is_relative_to(Path(raw).resolve()) or digest(path)!=row['sha256']:raise ValueError('Source integrity mismatch')
            observation=json.loads(path.read_text(encoding='utf-8'))
            dates=sorted(str(d) for d in observation['info']['dates'])
            if start_date and dates[0]<start_date:continue
            if end_date and dates[-1]>end_date:continue
            metadata,events=canonicalize(observation,path.stem)
            metadata['source_file_sha256']=row['sha256']
            store.ingest(observation,metadata,events)
            count+=1;attempts+=sum(e['kind']=='delivery' for e in events)
            if count>=limit:break
        if not count:raise ValueError('No eligible source matches')
        store.connection.execute('CREATE TABLE IF NOT EXISTS build_metadata (key TEXT PRIMARY KEY,value TEXT)')
        with store.connection:store.connection.execute('INSERT INTO build_metadata VALUES (?,?)',('dataset_id',manifest['dataset_id']))
        return {'matches':count,'attempts':attempts,'dataset_id':manifest['dataset_id'],'schema_version':1,
                'historical_event_timestamps':None,'network_calls':0,'start_date_filter':start_date,'end_date_filter':end_date}
    finally:store.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir',type=Path,required=True);parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--limit',type=int,default=100)
    parser.add_argument('--start-date');parser.add_argument('--end-date')
    args=parser.parse_args();print(json.dumps(import_subset(args.raw_dir,args.dataset,args.output,args.limit,start_date=args.start_date,end_date=args.end_date),indent=2))


if __name__=='__main__':main()
