"""Budgeted local manual/replay collector. No network and no public write surface."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone,date
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid
from .source_policy import decision
from ..pipeline.events import EventStore,checksum,encoded,validate_event
from ..pipeline.identities import local_id

STATES={'scheduled','in_progress','innings_break','paused','completed','abandoned'}


def manual_session(identifier,batting_first,bowling_first,match_date,gender='unknown',fmt='T20I',team_type='unknown'):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',identifier):raise ValueError('Invalid manual session identifier')
    date.fromisoformat(match_date)
    if fmt not in ('T20I','ODI'):raise ValueError('This helper needs explicit limited-overs innings; provide full Test metadata separately')
    if gender not in ('male','female','mixed','unknown') or team_type not in ('international','club','unknown'):raise ValueError('Explicit supported/unknown scope required')
    teams=[batting_first,bowling_first]
    if len(set(teams))!=2 or any(not isinstance(team,str) or not 1<=len(team)<=200 for team in teams):raise ValueError('Two distinct team names required in batting order')
    declaration={'id':identifier,'teams':teams,'date':match_date,'gender':gender,'format':fmt,'team_type':team_type}
    return {'schema_version':1,'match_id':'match:manual:'+identifier,'source_id':identifier,'source_hash':checksum(declaration),
            'dates':[match_date],'format':fmt,'gender':gender,'team_type':team_type,'balls_per_over':6,'teams':teams,
            'innings':[{'innings':i,'team':team,'team_id':local_id('team',identifier,team),'super_over':False,'source_target':None,'target_availability':'unknown'} for i,team in enumerate(teams,1)],
            'event_time_precision':'unknown','observed_at':None}


def manual_delivery(metadata,state,striker,non_striker,bowler,batter_runs=0,extras=None,wickets=None,event_time=None):
    extras=dict(extras or {});legal=not extras.get('wides') and not extras.get('noballs')
    attempt=state.get('next_attempt_number',state['attempts']+1);innings=state['innings'];bpo=metadata['balls_per_over']
    return {'schema_version':1,'match_id':metadata['match_id'],'innings':innings,'attempt':attempt,'kind':'delivery',
            'event_id':metadata['match_id']+'#i'+str(innings)+'/d'+str(attempt),'revision':1,'order':attempt*10,
            'over':state['legal_balls']//bpo,'over_legal_limit':bpo,'over_end':bool(legal and (state['legal_balls']+1)%bpo==0),
            'striker':striker,'non_striker':non_striker,'bowler':bowler,'runs':{'batter':batter_runs,'extras':sum(extras.values()),'total':batter_runs+sum(extras.values())},
            'extras':extras,'wickets':list(wickets or []),'source_hash':'assigned-at-ingest','event_time':event_time,'observed_at':None,'deleted':False}


class LocalCollector:
    def __init__(self,path,mode='manual',enabled=False,clock=time.time,minute_limit=60,day_limit=5000):
        from ..paths import PACKAGE_ROOT,PROJECT_ROOT
        self.path=Path(path).resolve()
        if any(self.path.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Collector store must be private')
        if mode not in ('manual','replay'):raise ValueError('Only local manual/replay source is approved')
        if not 1<=minute_limit<=60 or not 1<=day_limit<=5000:raise ValueError('Collector budget outside allowed bounds')
        self.path.parent.mkdir(parents=True,exist_ok=True);self.mode=mode;self.enabled=enabled;self.clock=clock
        self.minute_limit=minute_limit;self.day_limit=day_limit
        self.guard_path=self.path.with_suffix('.collector.sqlite3')
        self.guard=sqlite3.connect(self.guard_path,timeout=10)
        self.guard.executescript("""
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY,value INTEGER);
            INSERT OR IGNORE INTO settings VALUES ('kill',0);
            CREATE TABLE IF NOT EXISTS leases (match_id TEXT PRIMARY KEY,owner TEXT,until REAL);
            CREATE TABLE IF NOT EXISTS budgets (kind TEXT,window INTEGER,count INTEGER,PRIMARY KEY(kind,window));
            CREATE TABLE IF NOT EXISTS inputs (match_id TEXT,input_id TEXT,input_hash TEXT,captured_at TEXT,status TEXT,PRIMARY KEY(match_id,input_id));
            CREATE TABLE IF NOT EXISTS sessions (match_id TEXT PRIMARY KEY,mode TEXT,last_success REAL,payload TEXT);
        """)
        with self.guard:
            for name,value in (('minute_limit',minute_limit),('day_limit',day_limit)):
                self.guard.execute('INSERT OR IGNORE INTO settings VALUES (?,?)',(name,value))
                self.guard.execute('UPDATE settings SET value=MIN(value,?) WHERE name=?',(value,name))

    def close(self):self.guard.close()

    def kill(self,active=True):
        with self.guard:self.guard.execute("UPDATE settings SET value=? WHERE name='kill'",(int(active),))

    def _killed(self):return bool(self.guard.execute("SELECT value FROM settings WHERE name='kill'").fetchone()[0])

    def _validate(self,metadata,payload):
        if not isinstance(metadata,dict) or not isinstance(payload,dict):raise ValueError('Object session/observation required')
        if set(payload)-{'schema_version','match_id','observation_id','events','status','next_context','metadata_revision'}:raise ValueError('Unsupported observation fields')
        if metadata.get('schema_version')!=1 or not isinstance(metadata.get('match_id'),str) or not isinstance(metadata.get('innings'),list) or not 1<=len(metadata['innings'])<=32 or len(encoded(metadata))>65536:raise ValueError('Invalid bounded session')
        if metadata.get('format') not in ('T20I','ODI','Test') or metadata.get('gender') not in ('male','female','mixed','unknown') or type(metadata.get('balls_per_over')) is not int or not 1<=metadata['balls_per_over']<=8:raise ValueError('Invalid match rules/scope')
        if not isinstance(metadata.get('teams'),list) or len(metadata['teams'])!=2:raise ValueError('Two teams required')
        if not isinstance(metadata.get('dates'),list) or not 1<=len(metadata['dates'])<=10:raise ValueError('Explicit match dates required')
        for value in metadata['dates']:date.fromisoformat(value)
        for index,innings in enumerate(metadata['innings'],1):
            if innings.get('innings')!=index or not str(innings.get('team_id','')).startswith('team:') or type(innings.get('super_over')) is not bool:raise ValueError('Explicit innings identity required')
        if payload.get('schema_version')!=1 or payload.get('match_id')!=metadata.get('match_id'):raise ValueError('Collector match/schema mismatch')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',str(payload.get('observation_id',''))):raise ValueError('Bounded observation identifier required')
        if payload.get('status') not in STATES:raise ValueError('Explicit source status required')
        if self.mode=='manual' and not metadata['match_id'].startswith('match:manual:'):raise ValueError('Manual sessions need distinct manual identity namespace')
        if self.mode=='replay' and not metadata['match_id'].startswith('match:'):raise ValueError('Replay match identity required')
        if len(encoded(payload))>65536 or not isinstance(payload.get('events'),list) or len(payload['events'])>50:raise ValueError('Collector batch budget exceeded')
        if not payload['events'] and not payload.get('next_context') and payload['status']=='in_progress':raise ValueError('In-progress observation needs events or announced context')
        context=payload.get('next_context')
        if context:
            if set(context)-{'innings','attempt','striker','non_striker','bowler','not_started_confirmed','expected_state'}:raise ValueError('Unsupported announced context')
            if type(context.get('innings')) is not int or not 1<=context['innings']<=len(metadata['innings']) or type(context.get('attempt')) is not int or context['attempt']<1:raise ValueError('Invalid next-attempt sequence')
            if any(not str(context.get(name,'')).startswith('player:') for name in ('striker','non_striker','bowler')):raise ValueError('Stable announced participant IDs required')
            if len({context[name] for name in ('striker','non_striker','bowler')})!=3:raise ValueError('Distinct announced participants required')
            if type(context.get('not_started_confirmed')) is not bool:raise ValueError('Explicit not-started confirmation required')
            expected=context.get('expected_state',{})
            if set(expected)!={'runs','wickets','legal_balls'} or any(type(v) is not int or v<0 for v in expected.values()):raise ValueError('Explicit expected pre-attempt score required')

    def _reserve(self,metadata,payload):
        now=self.clock();mid=metadata['match_id'];input_id=payload['observation_id'];input_hash=checksum(payload)
        with self.guard:
            self.guard.execute('BEGIN IMMEDIATE')
            if not self.enabled or self._killed():return {'status':'stopped','reason':'disabled_or_killed'}
            expected_mode='local_manual' if self.mode=='manual' else 'historical_replay'
            if expected_mode not in decision()['permitted_modes']:return {'status':'stopped','reason':'source_not_approved'}
            session=self.guard.execute('SELECT mode,last_success FROM sessions WHERE match_id=?',(mid,)).fetchone()
            if session and session[0]!=self.mode:return {'status':'stopped','reason':'source_mode_changed'}
            if session and session[1] and session[1]>now:return {'status':'stopped','reason':'clock_regressed'}
            old=self.guard.execute('SELECT input_hash,captured_at,status FROM inputs WHERE match_id=? AND input_id=?',(mid,input_id)).fetchone()
            if old and old[0]!=input_hash:raise ValueError('Observation identifier has conflicting content')
            if old and datetime.fromisoformat(old[1]).timestamp()>now:return {'status':'stopped','reason':'clock_regressed'}
            if old and old[2]=='accepted':return {'status':'duplicate','observation_id':input_id,'captured_at':old[1],'external_calls':0}
            lease=self.guard.execute('SELECT owner,until FROM leases WHERE match_id=?',(mid,)).fetchone()
            if lease and lease[1]>now:return {'status':'deferred','reason':'single_owner_active','retry_after_seconds':max(1,int(lease[1]-now))}
            if not session and self.guard.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]>=128:return {'status':'stopped','reason':'session_budget'}
            # Operational counters retain seven days; raw observations never expire.
            for kind,width,limit in [('minute',60,self.guard.execute("SELECT value FROM settings WHERE name='minute_limit'").fetchone()[0]),('day',86400,self.guard.execute("SELECT value FROM settings WHERE name='day_limit'").fetchone()[0])]:
                window=int(now//width)
                count=self.guard.execute('SELECT count FROM budgets WHERE kind=? AND window=?',(kind,window)).fetchone()
                if count and count[0]>=limit:return {'status':'stopped','reason':kind+'_budget_exhausted'}
            for kind,width in [('minute',60),('day',86400)]:
                window=int(now//width)
                self.guard.execute('INSERT INTO budgets VALUES (?,?,1) ON CONFLICT(kind,window) DO UPDATE SET count=count+1',(kind,window))
                self.guard.execute('DELETE FROM budgets WHERE kind=? AND window<?',(kind,int((now-7*86400)//width)))
            captured=old[1] if old else datetime.fromtimestamp(now,timezone.utc).isoformat()
            self.guard.execute('INSERT OR IGNORE INTO inputs VALUES (?,?,?,?,?)',(mid,input_id,input_hash,captured,'reserved'))
            self.guard.execute('INSERT OR IGNORE INTO sessions VALUES (?,?,?,?)',(mid,self.mode,None,None))
            owner=uuid.uuid4().hex
            self.guard.execute('INSERT OR REPLACE INTO leases VALUES (?,?,?)',(mid,owner,now+30))
            return {'status':'reserved','owner':owner,'captured_at':captured}

    def ingest(self,metadata,payload):
        self._validate(metadata,payload);reservation=self._reserve(metadata,payload)
        if reservation['status']!='reserved':return reservation
        owner=reservation['owner'];captured=reservation['captured_at'];mid=metadata['match_id'];input_id=payload['observation_id']
        backoff=0
        try:
            if self._killed():return {'status':'stopped','reason':'kill_switch'}
            events=deepcopy(payload['events']);source_hash=checksum(payload)
            for event in events:
                event['source_hash']=source_hash;event['observed_at']=captured
                if event.get('event_time'):
                    from ..services.weather import utc
                    if utc(event['event_time'])>utc(captured):raise ValueError('Future event time')
                validate_event(event)
            lease=self.guard.execute('SELECT owner,until FROM leases WHERE match_id=?',(mid,)).fetchone()
            if not lease or lease[0]!=owner or lease[1]<=self.clock():return {'status':'deferred','reason':'lease_lost'}
            store=EventStore(self.path)
            try:
                if payload.get('metadata_revision'):store.register_metadata(metadata,payload['metadata_revision'],captured,source=self.mode)
                store.ingest(payload,metadata,events,source=self.mode,observed_at=captured)
            finally:store.close()
            lease=self.guard.execute('SELECT owner,until FROM leases WHERE match_id=?',(mid,)).fetchone()
            if not lease or lease[0]!=owner or lease[1]<=self.clock():return {'status':'deferred','reason':'lease_lost_after_commit'}
            snapshot={'mode':self.mode,'match_id':mid,'last_observation_id':input_id,'last_observed_at':captured,
                      'status':payload['status'],'next_context':deepcopy(payload.get('next_context')),'external_calls':0}
            if snapshot['next_context']:snapshot['next_context']['announced_at']=captured
            with self.guard:
                self.guard.execute("UPDATE inputs SET status='accepted' WHERE match_id=? AND input_id=?",(mid,input_id))
                timestamp=datetime.fromisoformat(captured).timestamp()
                self.guard.execute('UPDATE sessions SET last_success=?,payload=? WHERE match_id=? AND (last_success IS NULL OR last_success<=?)',(timestamp,encoded(snapshot),mid,timestamp))
            return {'status':'accepted','observation_id':input_id,'captured_at':captured,'events':len(events),'external_calls':0}
        except Exception:
            backoff=5
            with self.guard:self.guard.execute("UPDATE inputs SET status='failed' WHERE match_id=? AND input_id=?",(mid,input_id))
            raise
        finally:
            with self.guard:self.guard.execute('UPDATE leases SET until=? WHERE match_id=? AND owner=?',(self.clock()+backoff,mid,owner))

    def snapshot(self,match_id,stale_after_seconds=60):
        return _snapshot(self.guard,match_id,self.clock,stale_after_seconds)


def _snapshot(connection,match_id,clock,stale_after_seconds):
    row=connection.execute('SELECT payload,last_success FROM sessions WHERE match_id=?',(match_id,)).fetchone()
    if not row or not row[0]:return {'available':False,'stale':True,'reason':'no_confirmed_observation'}
    payload=json.loads(row[0]);age=clock()-row[1]
    payload.update(available=True,age_seconds=max(0,age),stale=age<0 or age>stale_after_seconds,killed=bool(connection.execute("SELECT value FROM settings WHERE name='kill'").fetchone()[0]))
    latest=connection.execute('SELECT status FROM inputs WHERE match_id=? ORDER BY captured_at DESC,rowid DESC LIMIT 1',(match_id,)).fetchone()
    lease=connection.execute('SELECT until FROM leases WHERE match_id=?',(match_id,)).fetchone()
    exhausted=False
    for kind,width in [('minute',60),('day',86400)]:
        limit=connection.execute('SELECT value FROM settings WHERE name=?',(kind+'_limit',)).fetchone()[0]
        count=connection.execute('SELECT count FROM budgets WHERE kind=? AND window=?',(kind,int(clock()//width))).fetchone()
        exhausted=exhausted or bool(count and count[0]>=limit)
    pending=connection.execute("SELECT 1 FROM inputs WHERE match_id=? AND status='reserved' LIMIT 1",(match_id,)).fetchone()
    payload['source_revision_counter']=connection.execute("SELECT COUNT(*) FROM inputs WHERE match_id=? AND status='accepted'",(match_id,)).fetchone()[0]
    pending_or_failed=bool(pending or (latest and latest[0]!='accepted') or (lease and lease[0]>clock()))
    payload['source_health']='killed' if payload['killed'] else 'budget_exhausted' if exhausted else 'ingest_pending_or_failed' if pending_or_failed else 'ok'
    payload['blocked']=payload['source_health']!='ok'

    return payload

def read_snapshot(path,match_id,clock=time.time,stale_after_seconds=60):
    guard=Path(path).resolve().with_suffix('.collector.sqlite3')
    if not guard.is_file():return {'available':False,'stale':True,'reason':'no_confirmed_observation'}
    connection=sqlite3.connect(guard.as_uri()+'?mode=ro',uri=True,timeout=2)
    try:return _snapshot(connection,match_id,clock,stale_after_seconds)
    finally:connection.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True);parser.add_argument('--mode',choices=['manual','replay'],default='manual')
    parser.add_argument('--session',type=Path);parser.add_argument('--observation',type=Path)
    parser.add_argument('--enable-local',action='store_true');parser.add_argument('--kill',action='store_true');parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();collector=LocalCollector(args.store,mode=args.mode,enabled=args.enable_local)
    try:
        if args.kill:collector.kill(True);print(json.dumps({'status':'killed'}));return 0
        if args.resume:collector.kill(False);print(json.dumps({'status':'resumed_local_policy_only'}));return 0
        if not args.session or not args.observation:parser.error('--session and --observation required for ingest')
        if args.session.stat().st_size>65536 or args.observation.stat().st_size>65536:raise ValueError('Input budget exceeded')
        result=collector.ingest(json.loads(args.session.read_text()),json.loads(args.observation.read_text()))
        print(json.dumps(result))
        return 0 if result['status'] in ('accepted','duplicate') else 2
    finally:collector.close()


if __name__=='__main__':raise SystemExit(main())
