"""Validate immutable JSON datasets and atomically select retained local versions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from ..services.json_io import atomic_json, read_json
from ..services.diagnostics import REQUIRED


def digest(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def identity(manifest):
    content={k:v for k,v in manifest.items() if k!='dataset_id'}
    return hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(directory,expected_manifest=None):
    directory=Path(directory).resolve()
    if expected_manifest and digest(directory/'manifest.json')!=expected_manifest:raise ValueError('Manifest digest mismatch')
    manifest=read_json(directory/'manifest.json')
    if manifest.get('manifest_version')!=1 or manifest.get('schema_version')!='2.0.1':raise ValueError('Unsupported dataset contract')
    if manifest.get('dataset_id')!=identity(manifest):raise ValueError('Dataset identity mismatch')
    outputs=manifest.get('outputs',{})
    if set(REQUIRED+('coverage.json','difference_report.json'))!=set(outputs):raise ValueError('Missing required artifacts')
    completed_count = None
    for name,checksum in outputs.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]*[.]json',name) or not re.fullmatch(r'[0-9a-f]{64}',checksum):raise ValueError('Invalid artifact name/hash')
        path=directory/name
        if path.is_symlink() or path.resolve().parent!=directory:raise ValueError('Artifact escapes dataset')
        if digest(path)!=checksum:raise ValueError('Artifact checksum mismatch')
        data=read_json(path)
        if not isinstance(data,dict):raise ValueError('Invalid artifact root')
        if name in ('players_index.json','completed_matches.json') and not data:raise ValueError('Empty required artifact')
        if name=='completed_matches.json' and (data.get('schema_version')!='2.0.1' or not isinstance(data.get('data'),list) or not data['data']):raise ValueError('Invalid completed-match schema')
        if name=='completed_matches.json':completed_count=len(data['data'])
    coverage=read_json(directory/'coverage.json')
    report=read_json(directory/'difference_report.json')
    count=coverage['accepted_matches']
    if count!=completed_count or sum(coverage['formats'].values())!=count:raise ValueError('Completed match coverage mismatch')
    if count!=report['accepted_matches'] or coverage['selected_inputs']!=len(manifest['inputs']):raise ValueError('Coverage mismatch')
    if len(manifest['inputs'])!=count+len(report['rejected']):raise ValueError('Unaccounted selected inputs')
    if manifest['inventory_files']!=len(manifest['inputs'])+len(manifest['excluded']):raise ValueError('Unaccounted raw inventory')
    return manifest


def promote(candidate,store,expected_manifest=None):
    candidate,store=Path(candidate).resolve(),Path(store).resolve()
    if candidate==store or store.is_relative_to(candidate):raise ValueError('Store must be outside candidate')
    from ..paths import PACKAGE_ROOT, PROJECT_ROOT
    if any(store==public or store.is_relative_to(public) for public in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Dataset store must not be public')
    manifest=validate(candidate,expected_manifest)
    version=manifest['dataset_id']
    versions=store/'versions';versions.mkdir(parents=True,exist_ok=True)
    destination=versions/version
    # Transactions serialize pointer changes; readers consume one immutable version
    # at process startup. No existing dataset/file is overwritten or deleted.
    connection=sqlite3.connect(store/'promotion.sqlite3',timeout=10)
    try:
        connection.execute('CREATE TABLE IF NOT EXISTS promotions (sequence INTEGER PRIMARY KEY, dataset_id TEXT, previous_id TEXT)')
        connection.execute('BEGIN IMMEDIATE')
        if destination.exists():validate(destination)
        else:
            staging=Path(tempfile.mkdtemp(prefix='candidate-',dir=store))
            for name in list(manifest['outputs'])+['manifest.json']:shutil.copy2(candidate/name,staging/name)
            validate(staging,expected_manifest)
            staging.rename(destination)
        pointer=read_json(store/'current.json') if (store/'current.json').exists() else {}
        previous=pointer.get('dataset_id')
        if previous==version:
            connection.rollback();return destination
        connection.execute('INSERT INTO promotions (dataset_id,previous_id) VALUES (?,?)',(version,previous))
        atomic_json(store/'current.json',{'dataset_id':version,'previous_id':previous})
        connection.commit()
    finally:connection.close()
    return destination


def selected(store):
    store=Path(store).resolve()
    pointer=read_json(store/'current.json');version=pointer.get('dataset_id','')
    if not re.fullmatch(r'[0-9a-f]{64}',version):raise ValueError('Invalid selected dataset')
    directory=store/'versions'/version
    if directory.is_symlink() or directory.resolve().parent!=(store/'versions').resolve():raise ValueError('Dataset version escapes store')
    manifest=validate(directory)
    if manifest['dataset_id']!=version:raise ValueError('Selected dataset identity mismatch')
    return directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['validate','promote'])
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--store',type=Path)
    parser.add_argument('--expected-manifest-sha256')
    args=parser.parse_args()
    if args.action=='promote':
        if not args.store:parser.error('--store required for promotion')
        result=promote(args.candidate,args.store,args.expected_manifest_sha256)
        print(json.dumps({'selected_dataset_id':result.name}))
    else:print(json.dumps({'dataset_id':validate(args.candidate,args.expected_manifest_sha256)['dataset_id']}))


if __name__=='__main__':main()
