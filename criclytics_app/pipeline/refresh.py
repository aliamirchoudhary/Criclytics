"""Bounded official Cricsheet refresh -> immutable bronze -> validated candidate.

No Git writes, deployment, serving-pointer change or model training/promotion.
"""
import argparse
from contextlib import closing,redirect_stdout
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import stat
import tempfile
import time
from urllib.robotparser import RobotFileParser
import uuid
import zipfile

import requests

from .artifacts import digest,validate as validate_candidate
from .rebuild import rebuild
from .schema import normalize_legacy_match,validate_match
from ..services.json_io import atomic_json
from ..paths import PACKAGE_ROOT,PROJECT_ROOT

ARCHIVES = {'tests_male_json':'Test','odis_male_json':'ODI','t20s_male_json':'T20I'}
UA = 'Criclytics/1.0 (+https://criclytics.aliamirchoudhary.workers.dev/)'
MAX_DOWNLOAD = 150*1024*1024
MAX_EXPANDED = 1024*1024*1024
MAX_STORE = 4*1024*1024*1024


def store_path(path):
    original=Path(path)
    if original.is_symlink():raise ValueError('Store must not be a symlink')
    path=original.resolve()
    if path==PROJECT_ROOT or any(path==p or path.is_relative_to(p) for p in
            (PACKAGE_ROOT,PROJECT_ROOT/'dist',PROJECT_ROOT/'data/raw',PROJECT_ROOT/'data/processed',PROJECT_ROOT/'data/static')):
        raise ValueError('Refresh store must be separate from source/public/original artifacts')
    marker=path/'cricsheet-refresh-store.json'
    if path.exists() and any(path.iterdir()) and not marker.is_file():
        raise ValueError('Refusing to write into an unrelated nonempty directory')
    path.mkdir(parents=True,exist_ok=True)
    if not marker.exists():atomic_json(marker,{'schema_version':1,'purpose':'cricsheet-refresh'})
    if json.loads(marker.read_text())!={'schema_version':1,'purpose':'cricsheet-refresh'}:
        raise ValueError('Invalid store marker')
    if sum(p.stat().st_size for p in path.rglob('*') if p.is_file())>MAX_STORE:
        raise ValueError('Private store budget exhausted; retain last good and review retention')
    return path


def check_source(session):
    registry=json.loads(Path(__file__).with_name('source_registry.json').read_text(encoding='utf-8'))
    source=next(r for r in registry['sources'] if r['id']=='cricsheet-json')
    if source['rights']!='allowed_with_attribution' or source['license']!='ODC-BY-1.0':
        raise ValueError('Historical source is not approved')
    with session.get('https://cricsheet.org/robots.txt',timeout=(10,30),allow_redirects=False) as response:
        if response.status_code==404:return
        if response.status_code!=200 or len(response.content)>65536:
            raise ValueError('Robots unavailable; stop without archive requests')
        robots=RobotFileParser();robots.parse(response.text.splitlines())
    if any(not robots.can_fetch(UA,'https://cricsheet.org/downloads/'+key+'.zip') for key in ARCHIVES):
        raise ValueError('Robots disallows an archive')


def fetch(session,root,key,previous,clock):
    bronze=root/'bronze';bronze.mkdir(exist_ok=True)
    headers={}
    cached=None
    if previous:
        checksum=previous.get('sha256','')
        if not re.fullmatch('[a-f0-9]{64}',checksum):raise ValueError('Invalid cached archive identity')
        candidate=bronze/(checksum+'.zip')
        if candidate.is_file() and not candidate.is_symlink() and digest(candidate)==checksum:
            cached=candidate
            for field,header in (('etag','If-None-Match'),('last_modified','If-Modified-Since')):
                value=previous.get(field)
                if value and len(value)<=512 and '\r' not in value and '\n' not in value:headers[header]=value
    url='https://cricsheet.org/downloads/'+key+'.zip'
    with session.get(url,headers=headers,timeout=(10,60),stream=True,allow_redirects=False) as response:
        if response.status_code==304:
            if cached is None:raise ValueError('304 without a verified retained archive')
            return {**previous,'checked_at':datetime.fromtimestamp(clock(),timezone.utc).isoformat(),'http_status':304},cached
        if response.status_code!=200:raise ValueError('Archive unavailable; no retry or fallback provider')
        if int(response.headers.get('Content-Length',0))>MAX_DOWNLOAD:raise ValueError('Archive byte budget exceeded')
        with tempfile.TemporaryDirectory(prefix='download-',dir=root) as temporary:
            path=Path(temporary)/'response.zip';total=0
            with path.open('wb') as stream:
                for chunk in response.iter_content(65536):
                    total+=len(chunk)
                    if total>MAX_DOWNLOAD:raise ValueError('Archive byte budget exceeded')
                    stream.write(chunk)
            checksum=digest(path);destination=bronze/(checksum+'.zip')
            # Full member/schema validation happens before source state advances.
            if not destination.exists():path.replace(destination)
            elif destination.is_symlink():raise ValueError('Archive symlink collision')
            elif digest(destination)!=checksum:
                quarantine=root/'quarantine';quarantine.mkdir(exist_ok=True)
                destination.replace(quarantine/(checksum+'-'+uuid.uuid4().hex+'.zip'))
                path.replace(destination)
    now=datetime.fromtimestamp(clock(),timezone.utc).isoformat()
    return {'sha256':checksum,'source_url':url,'license':'ODC-BY-1.0',
        'etag':response.headers.get('ETag'),'last_modified':response.headers.get('Last-Modified'),
        'received_at':now,'checked_at':now,'http_status':200,'bytes':total},destination


def extract(archive,destination,folder):
    """Exact authoritative snapshot. Never merge retained older match files."""
    destination.mkdir(parents=True)
    rows={};names=set();expanded=0
    with zipfile.ZipFile(archive) as source:
        members=source.infolist()
        if len(members)>12010:raise ValueError('Archive member budget exceeded')
        for member in members:
            name=member.filename
            mode=member.external_attr>>16
            if (not name or len(name)>100 or '/' in name or '\\' in name or name in names
                    or member.is_dir() or stat.S_ISLNK(mode) or member.flag_bits&1):
                raise ValueError('Unsafe or duplicate archive member')
            names.add(name);expanded+=member.file_size
            if member.file_size>8*1024*1024 or expanded>MAX_EXPANDED or member.file_size>max(1,member.compress_size)*2000:
                raise ValueError('Archive expansion budget exceeded')
            if not re.fullmatch(r'[0-9]{1,12}[.]json',name):
                if name.lower() in ('readme.txt','readme','license.txt','licence.txt'):continue
                raise ValueError('Unexpected archive member')
            raw=source.read(member)  # CRC checked; bounded by declared member limit
            match=json.loads(raw)
            normalize_legacy_match(match);validate_match(match)
            info=match['info']
            expected='T20' if ARCHIVES[folder]=='T20I' else ARCHIVES[folder]
            if info.get('gender')!='male' or info.get('team_type')!='international' or info.get('match_type')!=expected:
                raise ValueError('Archive population differs from declared source scope')
            (destination/name).write_bytes(raw)
            rows[folder+'/'+name]=hashlib.sha256(raw).hexdigest()
    if len(rows)<1:raise ValueError('Empty authoritative archive')
    return rows


def refresh(root,session=None,clock=time.time,build_candidate=True):
    root=store_path(root);owner=uuid.uuid4().hex;now=clock()
    latest_path=root/('latest.json' if build_candidate else 'latest-source.json')
    previous=json.loads(latest_path.read_text()) if latest_path.exists() else {}
    connection=sqlite3.connect(root/'jobs.sqlite3',timeout=2)
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS lease(id INTEGER PRIMARY KEY,owner TEXT,expires REAL)')
        connection.execute('BEGIN IMMEDIATE')
        row=connection.execute('SELECT owner,expires FROM lease WHERE id=1').fetchone()
        if row and row[1]>now:raise ValueError('Another refresh owns the lease')
        connection.execute('INSERT OR REPLACE INTO lease VALUES(1,?,?)',(owner,now+1800));connection.commit()
        if previous and now-previous['checked_epoch']<23*3600:
            return {'status':'not_due','candidate_id':previous.get('candidate_id'),'network_calls':0}
        with closing(session or requests.Session()) as client:
            client.headers.update({'User-Agent':UA})
            check_source(client)
            stamp=datetime.fromtimestamp(now,timezone.utc).isoformat()
            sources={};inputs={}
            with tempfile.TemporaryDirectory(prefix='snapshot-',dir=root) as temporary:
                raw_root=Path(temporary)/'raw'
                for key in ARCHIVES:
                    source_state=root/'sources'/(key+'.json')
                    retained=json.loads(source_state.read_text()) if source_state.exists() else previous.get('sources',{}).get(key)
                    source,path=fetch(client,root,key,retained,clock)
                    sources[key]=source
                    inputs.update(extract(path,raw_root/key,key))
                    source_state.parent.mkdir(exist_ok=True)
                    atomic_json(source_state,source)
                code={p.name:digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))}
                identity=hashlib.sha256(json.dumps({'inputs':inputs,'code':code,
                    'registry':digest(Path(__file__).with_name('source_registry.json'))},sort_keys=True).encode()).hexdigest()
                old_inputs=previous.get('inputs',{})
                report={'schema_version':1,'source':'cricsheet-json','started_at':stamp,
                    'source_publication_time':'unknown; HTTP Last-Modified is not each match publication',
                    'sources':sources,'inputs':inputs,'snapshot_id':identity,'candidate_id':None,
                    'changes':{'added':sum(k not in old_inputs for k in inputs),
                        'revised':sum(k in old_inputs and old_inputs[k]!=v for k,v in inputs.items()),
                        'withdrawn':sorted(set(old_inputs)-set(inputs))},
                    'attribution':'Data from Cricsheet, https://cricsheet.org/; ODC-BY1.0',
                    'automatic_serving_promotion':False,'automatic_model_promotion':False}
                if build_candidate:
                    retained=previous.get('candidate_path')
                    if identity==previous.get('snapshot_id') and retained:
                        candidate=root/retained
                        if candidate.resolve().parent.parent!=root/'candidates':raise ValueError('Candidate path escapes store')
                        manifest=validate_candidate(candidate)
                        if manifest['dataset_id']!=previous.get('candidate_id'):raise ValueError('Retained candidate identity mismatch')
                        report.update(candidate_path=retained,candidate_id=manifest['dataset_id'],status='unchanged')
                    else:
                        candidate=root/'candidates'/owner/'gold'
                        # Legacy progress includes Unicode symbols unsupported by
                        # some Windows consoles. Keep the job's JSON output clean.
                        with redirect_stdout(io.StringIO()):rebuild(raw_root,candidate)
                        manifest=validate_candidate(candidate)
                        coverage=json.loads((candidate/'coverage.json').read_text())
                        if coverage['rejected_files'] or set(coverage['formats'])!=set(ARCHIVES.values()):
                            raise ValueError('Incomplete combined candidate; previous checkpoint retained')
                        if previous.get('accepted_matches') and coverage['accepted_matches']<previous['accepted_matches']*.8:
                            raise ValueError('Coverage collapsed; withdrawal review required')
                        report.update(candidate_path=candidate.relative_to(root).as_posix(),candidate_id=manifest['dataset_id'],
                            accepted_matches=coverage['accepted_matches'],data_cutoff=coverage['data_cutoff'],status='candidate_ready')
                    for key in ('accepted_matches','data_cutoff'):
                        if key not in report and key in previous:report[key]=previous[key]
                else:report['status']='source_validated_only'
                if clock()>now+25*60:raise ValueError('Job deadline exceeded; checkpoint retained')
                if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>MAX_STORE:
                    raise ValueError('Store byte budget exceeded; checkpoint retained')
                report.update(checked_at=datetime.fromtimestamp(clock(),timezone.utc).isoformat(),checked_epoch=clock())
                runs=root/'runs';runs.mkdir(exist_ok=True)
                atomic_json(runs/(owner+'.json'),report)
                atomic_json(latest_path,report)
                return report
    finally:
        connection.rollback()
        with connection:connection.execute('DELETE FROM lease WHERE id=1 AND owner=?',(owner,))
        connection.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--validate-source-only',action='store_true')
    args=parser.parse_args()
    try:
        report=refresh(args.store,build_candidate=not args.validate_source_only)
    except Exception as error:
        # Provider error strings can contain URLs; never print exception text.
        print(json.dumps({'status':'failed','error_type':type(error).__name__,'previous_selection_preserved':True}))
        raise SystemExit(1) from None
    print(json.dumps({k:report[k] for k in ('status','candidate_id','accepted_matches','data_cutoff','changes') if k in report}))


if __name__=='__main__':main()
