"""Source-cutoff state reconciliation and bounded derived-state history, never raw rewrites."""
from collections import OrderedDict,defaultdict
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3
import threading
import time
from .weather import utc
from .annotations import annotation_context,position
from ..integrations.collector import read_snapshot
from ..pipeline.events import EventStore,initial_state,apply_event,checksum,encoded
from ..pipeline.features import History,LocalHistory,vector


class StateLedger:
    def __init__(self,path):
        from ..paths import PACKAGE_ROOT,PROJECT_ROOT
        path=Path(path).resolve()
        if any(path.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('State ledger must be private')
        path.parent.mkdir(parents=True,exist_ok=True);self.connection=sqlite3.connect(path,timeout=5)
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS state_snapshots (state_id TEXT PRIMARY KEY,match_id TEXT NOT NULL,source_cutoff TEXT NOT NULL,payload TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS state_match ON state_snapshots(match_id);
            CREATE TABLE IF NOT EXISTS issued_forecasts (forecast_id TEXT PRIMARY KEY,match_id TEXT NOT NULL,target_event_id TEXT NOT NULL,state_id TEXT NOT NULL,model_id TEXT NOT NULL,issued_at TEXT NOT NULL,payload TEXT NOT NULL,replaces TEXT,UNIQUE(state_id,model_id));
            CREATE INDEX IF NOT EXISTS forecast_match ON issued_forecasts(match_id);
            CREATE TABLE IF NOT EXISTS current_state (match_id TEXT PRIMARY KEY,state_id TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS state_invalidations (old_state_id TEXT,new_state_id TEXT,reason TEXT,recorded_at TEXT,PRIMARY KEY(old_state_id,new_state_id,reason));
        """)

    def close(self):self.connection.close()

    def record(self,core,reasons=(),now=None):
        state_id=checksum(core);mid=core['match_id'];payload=encoded(core)
        if len(payload)>131072:raise ValueError('State payload budget exceeded')
        recorded=now or datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            old=self.connection.execute('SELECT payload FROM state_snapshots WHERE state_id=?',(state_id,)).fetchone()
            if old and old[0]!=payload:raise ValueError('Immutable state identity conflict')
            if not old and (self.connection.execute('SELECT COUNT(*) FROM state_snapshots WHERE match_id=?',(mid,)).fetchone()[0]>=10000 or self.connection.execute('SELECT COUNT(*) FROM state_snapshots').fetchone()[0]>=100000):raise ValueError('Derived-state retention budget exceeded')
            self.connection.execute('INSERT OR IGNORE INTO state_snapshots VALUES (?,?,?,?)',(state_id,mid,core['source_cutoff'],payload))
            previous=self.connection.execute('SELECT c.state_id,s.payload FROM current_state c JOIN state_snapshots s ON s.state_id=c.state_id WHERE c.match_id=?',(mid,)).fetchone()
            if previous:
                old_core=json.loads(previous[1])
                old_key=(utc(old_core['source_cutoff']).timestamp(),old_core.get('source_revision_counter',0))
                new_key=(utc(core['source_cutoff']).timestamp(),core.get('source_revision_counter',0))
                if old_key>new_key:return state_id
            if previous and previous[0]!=state_id:
                self.connection.execute('INSERT OR IGNORE INTO state_invalidations VALUES (?,?,?,?)',(previous[0],state_id,'source_or_context_revision',recorded))
            for reason in sorted(set(reasons)):
                self.connection.execute('INSERT OR IGNORE INTO state_invalidations VALUES (?,?,?,?)',(state_id,'',reason,recorded))
            self.connection.execute('INSERT OR REPLACE INTO current_state VALUES (?,?)',(mid,state_id))
        return state_id


    def issue(self,content,issued_at):
        for key in ('match_id','target_event_id','state_id','model_id'):
            if not isinstance(content.get(key),str):raise ValueError('Forecast identity required')
        utc(issued_at);payload=encoded(content);forecast_id=checksum(content)
        if len(payload)>131072:raise ValueError('Forecast payload budget exceeded')
        with self.connection:
            self.connection.execute('BEGIN IMMEDIATE')
            state=self.connection.execute('SELECT match_id,source_cutoff,payload FROM state_snapshots WHERE state_id=?',(content['state_id'],)).fetchone()
            if not state or state[0]!=content['match_id']:raise ValueError('Forecast requires recorded matching state')
            current=self.connection.execute('SELECT state_id FROM current_state WHERE match_id=?',(content['match_id'],)).fetchone()
            if not current or current[0]!=content['state_id']:raise ValueError('Superseded state cannot issue a new forecast')
            if utc(issued_at)<utc(state[1]) or json.loads(state[2])['target_event_id']!=content['target_event_id']:raise ValueError('Forecast cutoff/target contradicts state')
            old=self.connection.execute('SELECT forecast_id,payload FROM issued_forecasts WHERE state_id=? AND model_id=?',(content['state_id'],content['model_id'])).fetchone()
            if old:
                if old[1]!=payload:raise ValueError('Immutable issued forecast conflict')
                return self.forecast(old[0])
            if self.connection.execute('SELECT COUNT(*) FROM issued_forecasts WHERE match_id=?',(content['match_id'],)).fetchone()[0]>=10000 or self.connection.execute('SELECT COUNT(*) FROM issued_forecasts').fetchone()[0]>=100000:raise ValueError('Forecast retention budget exceeded')
            previous=self.connection.execute('SELECT forecast_id FROM issued_forecasts WHERE match_id=? AND target_event_id=? ORDER BY rowid DESC LIMIT 1',(content['match_id'],content['target_event_id'])).fetchone()
            replaces=previous[0] if previous else None
            self.connection.execute('INSERT INTO issued_forecasts VALUES (?,?,?,?,?,?,?,?)',(forecast_id,content['match_id'],content['target_event_id'],content['state_id'],content['model_id'],issued_at,payload,replaces))
        return self.forecast(forecast_id)

    def forecast(self,forecast_id):
        row=self.connection.execute('SELECT issued_at,payload,replaces FROM issued_forecasts WHERE forecast_id=?',(forecast_id,)).fetchone()
        return {'forecast_id':forecast_id,'issued_at':row[0],'content':json.loads(row[1]),'replaces_forecast_id':row[2]} if row else None

    def history(self,match_id,limit=50):
        if not 1<=limit<=200:raise ValueError('History limit must be1..200')
        rows=self.connection.execute('SELECT forecast_id FROM issued_forecasts WHERE match_id=? ORDER BY rowid DESC LIMIT ?',(match_id,limit)).fetchall()
        return [self.forecast(row[0]) for row in rows]


class Reconciler:
    def __init__(self,path,clock=time.time,history=None,history_known_at=None,contexts=None):
        self.path=Path(path).resolve();self.clock=clock;self.history=deepcopy(history);self.history_known_at=history_known_at;self.contexts=contexts
        self._cache=OrderedDict();self._lock=threading.RLock();self.rebuilds=0

    def get(self,match_id):
        source=read_snapshot(self.path,match_id,clock=self.clock)
        if not source.get('available'):return {'available':False,'forecast_allowed':False,'blocked_reasons':[source.get('reason','source_unavailable')],'state_id':None,'mode':None}
        cutoff=source['last_observed_at'];context_records=[]
        if self.contexts:context_records=self.contexts.eligible(match_id,cutoff,require_ingested=True)
        key=(match_id,source['last_observation_id'],source.get('source_revision_counter',0),cutoff,checksum(context_records))
        with self._lock:
            cached=self._cache.get(key)
            if cached is None:
                core,reasons=self._build(match_id,source,context_records)
                self._cache[key]=(core,reasons);self.rebuilds+=1
                while len(self._cache)>16:self._cache.popitem(last=False)
            else:self._cache.move_to_end(key);core,reasons=cached
            reasons=list(reasons)
        if source.get('stale'):reasons.append('stale_source')
        if source.get('blocked'):reasons.append(source.get('source_health','source_blocked'))
        if source['status']!='in_progress':reasons.append('source_'+source['status'])
        announced=source.get('next_context')
        if announced:
            age=self.clock()-utc(announced['announced_at']).timestamp()
            if age<0 or age>15:reasons.append('next_announcement_expired')
        if not core:return {'available':False,'forecast_allowed':False,'blocked_reasons':sorted(set(reasons)),'state_id':None,'mode':source['mode']}
        return {'available':True,'forecast_allowed':not reasons,'blocked_reasons':sorted(set(reasons)),
                'state_id':checksum(core),'core':deepcopy(core),'mode':source['mode'],'source_age_seconds':source['age_seconds'],
                'source_health':source.get('source_health'),'event_lag_seconds':core.get('event_lag_seconds')}

    def _build(self,match_id,source,context_records):
        reasons=[];cutoff=source['last_observed_at'];store=EventStore(self.path,readonly=True)
        try:
            store.connection.execute('BEGIN')
            metadata=store.metadata(match_id,as_of=cutoff)
            if not metadata:return None,['missing_match_metadata']
            events=list(store.events(match_id,as_of=cutoff,allow_unknown=source['mode']=='replay',include_deleted=True))
            if len(events)>20000:return None,['event_budget_exceeded']
        finally:store.close()
        announced=source.get('next_context');logical=defaultdict(set);states={};locals={}
        for info in metadata['innings']:
            states[info['innings']]=initial_state(metadata,info['innings']);locals[info['innings']]=LocalHistory()
        for event in events:
            if event['innings'] not in states:reasons.append('undeclared_innings');continue
            if event['kind']=='delivery':
                try:mid,innings,attempt=position(event['event_id'])
                except ValueError:reasons.append('noncanonical_attempt_identity');continue
                if (mid,innings,attempt)!=(match_id,event['innings'],event['attempt']) or event['order']!=event['attempt']*10:reasons.append('source_order_conflict')
                logical[event['innings']].add(event['attempt'])
        for innings,numbers in logical.items():
            if numbers!=set(range(1,max(numbers)+1)):reasons.append('missing_delivery_attempt')
        latest_event_time=None
        for event in events:
            innings=event['innings']
            if innings not in states or event.get('deleted'):continue
            state=states[innings]
            if event['kind']!='delivery' and event['attempt']>max(logical.get(innings) or {0})+1:continue
            if event['kind']=='delivery':
                if state['innings_complete']:reasons.append('delivery_after_innings_end')
                locals[innings].observe(event)
                if event.get('event_time'):
                    latest_event_time=max(latest_event_time or event['event_time'],event['event_time'],key=utc)
            apply_event(state,event)
            if state['closing_total_match'] is False:reasons.append('closing_score_conflict')
            if state['wickets']>10:reasons.append('invalid_wicket_count')
        active=announced['innings'] if announced else max((i for i,s in states.items() if s['attempts']),default=1)
        if active not in states:return None,reasons+['undeclared_active_innings']
        state=states[active];state['next_attempt_number']=max(logical.get(active) or {0})+1
        if active>1 and not states[active-1]['innings_complete']:reasons.append('previous_innings_not_confirmed_complete')
        if active>1 and metadata['format']!='Test' and not state['super_over'] and state['target'] is None and states[active-1]['innings_complete']:
            state.update(target=states[active-1]['runs']+1,target_basis='derived_prior_innings_unverified')
        features=None
        if not announced:reasons.append('missing_next_participants')
        else:
            if not announced['not_started_confirmed']:reasons.append('next_attempt_not_confirmed_open')
            if announced['attempt']!=state['next_attempt_number']:reasons.append('next_attempt_sequence_mismatch')
            if any(state[key]!=value for key,value in announced['expected_state'].items()):reasons.append('announced_score_conflict')
            if state['innings_complete'] or state['wickets']>=10:reasons.append('innings_complete')
            if state['target_verified'] and state['runs']>=state['target']:reasons.append('target_reached')
            schedule=state.get('scheduled_balls') if state.get('scheduled_balls_verified') else None
            if schedule is not None and state['legal_balls']>=schedule:reasons.append('scheduled_balls_exhausted')
            history=self.history or History()
            if self.history and (not self.history_known_at or utc(self.history_known_at)>utc(cutoff) or history.last_completed_date and history.last_completed_date>=metadata['dates'][0]):
                reasons.append('prior_history_not_available_at_cutoff');history=History()
            features=vector(state,{key:announced[key] for key in ('striker','non_striker','bowler')},history,locals[active],metadata)
        target_id=match_id+'#i'+str(active)+'/d'+str(state['next_attempt_number'])
        annotations=annotation_context(context_records,target_id)
        if len(annotations['observations'])>100:
            annotations['observations']=annotations['observations'][:100];annotations['observations_truncated']=True
        core={'schema_version':1,'feature_schema':1,'match_id':match_id,'mode':source['mode'],'source_cutoff':cutoff,
              'source_observation_id':source['last_observation_id'],'source_revision_counter':source.get('source_revision_counter',0),'source_status':source['status'],
              'source_revision_hash':checksum(events),'metadata_hash':checksum(metadata),
              'scope':{key:metadata.get(key) for key in ('format','gender','team_type','dates')},'teams':metadata['teams'],
              'innings':[states[index] for index in sorted(states)],'active_innings':active,
              'next_context':announced,'target_event_id':target_id,'features':features,'annotations':annotations,
              'event_lag_seconds':max(0,(utc(cutoff)-utc(latest_event_time)).total_seconds()) if latest_event_time else None,
              'history_scope':'explicit prior archive' if self.history else 'session only; prior history unavailable',
              'context_coverage':{'weather':'not_in_model','lineup_pitch_home':'not_in_model','annotations':'not_in_model'}}
        return core,reasons
