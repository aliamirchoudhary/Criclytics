"""Local immutable as-of context ledger; no inferred XI, pitch tracking or home advantage."""
from contextlib import nullcontext
import json
import math
from pathlib import Path
import sqlite3
from datetime import datetime,timezone
from .weather import utc
from ..pipeline.events import encoded

KINDS={'lineup','substitution','pitch_report','venue_affiliation','fielding','incident',
       'weather_observation','captaincy','crowd_event'}


def validate(record):
    if record.get('schema_version')!=1 or record.get('kind') not in KINDS:raise ValueError('Unsupported context contract')
    for key in ('record_id','match_id','source','observer'):
        if not isinstance(record.get(key),str) or not 1<=len(record[key])<=300:raise ValueError('Context provenance required')
    if type(record.get('revision')) is not int or record['revision']<1:raise ValueError('Context revision required')
    for key in ('published_at','observed_at','effective_at'):utc(record[key])
    if record.get('scope') not in ('public','private'):raise ValueError('Explicit access scope required')
    if record['scope']=='private' and not record.get('owner_id'):raise ValueError('Private ownership required')
    value=record['value'];kind=record['kind']
    if kind in ('weather_observation','captaincy','crowd_event'):
        from .context_availability import validate_extension
        validate_extension(record)
    if kind=='lineup':
        players=value.get('player_ids',[])
        if len(players)!=11 or len(set(players))!=11 or any(not p.startswith('player:') for p in players):raise ValueError('Announced XI requires11 distinct stable players')
        if not value.get('team_id'):raise ValueError('Lineup team required')
        if set(value.get('roles',{}))-set(players):raise ValueError('Role not in announced XI')
    if kind=='substitution':
        if not value.get('team_id') or value.get('out_id')==value.get('in_id') or not all(str(value.get(k,'')).startswith('player:') for k in ('out_id','in_id')):raise ValueError('Invalid substitution identity')
    if kind=='pitch_report':
        if value.get('quality') not in ('observer_report','instrument_measured','unverified') or not value.get('venue_id'):raise ValueError('Pitch source/quality required')
        if value.get('quality')=='instrument_measured':
            if not value.get('instrument_id') or not value.get('measurement_method'):raise ValueError('Tracking instrument/method required')
            for name,low,high in (('bounce_cm',0,1000),('line_m',-20,20),('length_m',0,50)):
                number=value.get(name)
                if number is not None and (not isinstance(number,(int,float)) or not math.isfinite(number) or not low<=number<=high):raise ValueError('Invalid tracking measurement')
        if value.get('quality')!='instrument_measured' and any(value.get(k) is not None for k in ('bounce_cm','line_m','length_m')):raise ValueError('Reported pitch tags are not measured tracking')
    if kind=='venue_affiliation' and (value.get('status') not in ('home','away','neutral','unknown') or not value.get('venue_id') or not value.get('team_id')):raise ValueError('Explicit sourced venue affiliation required')
    if kind in ('fielding','incident'):
        from .annotations import validate_annotation
        validate_annotation(record)
    return record


class ContextLedger:
    def __init__(self,path,read_only=False):
        from ..paths import PACKAGE_ROOT,PROJECT_ROOT
        self.path=Path(path).resolve()
        if any(self.path.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Context ledger must be private')
        if read_only:
            self.connection=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True,timeout=.25)
            return
        self.path.parent.mkdir(parents=True,exist_ok=True);self.connection=sqlite3.connect(self.path,timeout=10)
        self.connection.executescript("""CREATE TABLE IF NOT EXISTS context_records (
            record_id TEXT NOT NULL,revision INTEGER NOT NULL,match_id TEXT NOT NULL,kind TEXT NOT NULL,
            available_at REAL NOT NULL,payload TEXT NOT NULL,ingested_at TEXT,PRIMARY KEY(record_id,revision));
            CREATE INDEX IF NOT EXISTS context_cutoff ON context_records(match_id,available_at);
        """)
        if 'ingested_at' not in {row[1] for row in self.connection.execute('PRAGMA table_info(context_records)')}:
            self.connection.execute('ALTER TABLE context_records ADD COLUMN ingested_at TEXT')
            self.connection.commit()

    def close(self):self.connection.close()

    def add(self,record,commit=True):
        validate(record);payload=encoded(record)
        if len(payload)>16384:raise ValueError('Context payload budget exceeded')
        available=max(utc(record[k]).timestamp() for k in ('published_at','observed_at','effective_at'))
        with self.connection if commit else nullcontext():
            original=self.connection.execute('SELECT payload FROM context_records WHERE record_id=? ORDER BY revision LIMIT 1',(record['record_id'],)).fetchone()
            if original:
                first=json.loads(original[0])
                if any(first.get(key)!=record.get(key) for key in ('match_id','kind','owner_id')):raise ValueError('Context identity/owner is immutable')
            old=self.connection.execute('SELECT payload FROM context_records WHERE record_id=? AND revision=?',(record['record_id'],record['revision'])).fetchone()
            if old and old[0]!=payload:raise ValueError('Conflicting immutable context revision')
            count=self.connection.execute('SELECT COUNT(*) FROM context_records WHERE match_id=?',(record['match_id'],)).fetchone()[0]
            if not old and count>=10000:raise ValueError('Per-match context budget exceeded')
            self.connection.execute('INSERT OR IGNORE INTO context_records (record_id,revision,match_id,kind,available_at,payload,ingested_at) VALUES (?,?,?,?,?,?,?)',(record['record_id'],record['revision'],record['match_id'],record['kind'],available,payload,datetime.now(timezone.utc).isoformat()))

    def eligible(self,match_id,cutoff,owner_id=None,require_ingested=False):
        when=utc(cutoff).timestamp()
        ingestion=" AND r.ingested_at IS NOT NULL AND r.ingested_at<=?" if require_ingested else ""
        parameters=(match_id,when,utc(cutoff).isoformat(timespec='microseconds')) if require_ingested else (match_id,when)
        rows=self.connection.execute("SELECT c.payload FROM context_records c WHERE c.match_id=? AND c.revision=(SELECT MAX(revision) FROM context_records r WHERE r.record_id=c.record_id AND r.available_at<=?"+ingestion+") ORDER BY c.available_at,c.record_id LIMIT 1025",parameters).fetchall()
        if len(rows)>1024:raise ValueError('Context selection budget exceeded')
        result=[]
        for row in rows:
            record=json.loads(row[0])
            if record['scope']=='private' and record['owner_id']!=owner_id:continue
            if not record.get('deleted'):result.append(record)
        return result


def lineup_snapshot(records,team_id):
    eligible=[r for r in records if r['kind']=='lineup' and r['value']['team_id']==team_id]
    if not eligible:return {'available':False,'players':None,'roles':None,'reason':'No eligible announced XI'}
    base=max(eligible,key=lambda r:(utc(r['effective_at']),utc(r['observed_at']),r['record_id']))
    players=list(base['value']['player_ids']);roles=dict(base['value'].get('roles',{}));applied=[]
    substitutions=sorted((r for r in records if r['kind']=='substitution' and r['value']['team_id']==team_id and utc(r['effective_at'])>=utc(base['effective_at'])),key=lambda r:(utc(r['effective_at']),r['record_id']))
    for record in substitutions:
        value=record['value']
        if value['out_id'] not in players or value['in_id'] in players:return {'available':False,'players':None,'roles':None,'reason':'Conflicting substitution requires review'}
        players[players.index(value['out_id'])]=value['in_id'];roles.pop(value['out_id'],None)
        if value.get('role'):roles[value['in_id']]=value['role']
        applied.append(record['record_id'])
    return {'available':True,'players':players,'roles':roles,'base_record':base['record_id'],'substitutions':applied}


def pitch_context(records,venue_id):
    rows=[r for r in records if r['kind']=='pitch_report' and r['value']['venue_id']==venue_id]
    if not rows:return {'available':False,'quality':'unknown','measurements':None,'tags':None}
    latest=max(rows,key=lambda r:(utc(r['effective_at']),utc(r['observed_at']),r['record_id']))
    value=latest['value']
    return {'available':True,'quality':value['quality'],'tags':value.get('tags'),
            'measurements':{k:value.get(k) for k in ('bounce_cm','line_m','length_m')} if value['quality']=='instrument_measured' else None,
            'source':latest['source'],'record_id':latest['record_id']}


def venue_affiliation(records,venue_id,team_id):
    rows=[r for r in records if r['kind']=='venue_affiliation' and r['value']['venue_id']==venue_id and r['value']['team_id']==team_id]
    if not rows:return {'status':'unknown','source':None}
    latest=max(rows,key=lambda r:(utc(r['effective_at']),utc(r['observed_at']),r['record_id']))
    return {'status':latest['value']['status'],'source':latest['source']}
