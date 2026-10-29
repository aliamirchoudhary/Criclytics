"""Prepare reviewed non-commercial portraits privately; never hotlink or publish a dataset."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--download', action='store_true', help='Use reviewed CricketData non-commercial image-hosting instructions')
    args = parser.parse_args()
    from criclytics_app.paths import PACKAGE_ROOT, PROJECT_ROOT
    output = args.output.resolve()
    if any(output == p or output.is_relative_to(p) for p in (PACKAGE_ROOT/'static', PROJECT_ROOT/'dist')):
        raise ValueError('Provider originals must remain outside public Git/static artifacts')
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a fresh private output directory')
    metadata = json.loads(args.metadata.read_text(encoding='utf-8'))
    entities = json.loads(args.registry.read_text(encoding='utf-8'))['entities']['player']
    scope = 'Non-commercial editorial display only; downloaded per provider hosting instructions. No public dataset redistribution.'
    manifest = {'schema_version':1, 'source_terms':'https://cricketdata.org/terms-of-use/',
                'reviewed_at':'2026-10-29', 'use_scope':scope, 'players':[]}
    skipped = []
    planned = []
    for name, item in metadata.items():
        source = urlsplit(item.get('image_url', ''))
        if source.scheme != 'https' or source.hostname != 'h.cricapi.com' or source.query or source.username or source.password:
            continue
        candidates = [key for key, entity in entities.items() if
                      {name.casefold(), item.get('full_name','').casefold()} &
                      ({entity['name'].casefold()} | {str(a).casefold() for a in entity.get('aliases',[])})]
        if len(candidates) != 1:
            skipped.append({'name':name, 'reason':'identity_not_unique'})
            continue
        planned.append((candidates[0], name, item))
    if not args.download:
        print(json.dumps({'eligible_unique_identities':len(planned), 'skipped':len(skipped), 'network_requests':0}))
        return
    import requests
    output.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        session.headers['User-Agent'] = 'Criclytics non-commercial editorial media preparation'
        for key, name, item in planned[:100]:
            try:
                response = session.get(item['image_url'], timeout=15, allow_redirects=False)
                if response.status_code == 429:
                    skipped.append({'name':name, 'reason':'rate_limited_stop'})
                    break
                response.raise_for_status()
                raw = response.content
                if len(raw) > 2*1024*1024 or not raw.startswith(b'\xff\xd8\xff'):
                    skipped.append({'name':name, 'reason':'not_bounded_jpeg'})
                    continue
                filename = key.rsplit(':',1)[1]+'.jpg'
                (output/filename).write_bytes(raw)
                manifest['players'].append({'identity_id':key, 'name':item.get('full_name') or name,
                    'file':filename, 'sha256':hashlib.sha256(raw).hexdigest(),
                    'source':item['image_url'], 'use_scope':scope})
            except requests.RequestException as error:
                skipped.append({'name':name, 'reason':type(error).__name__})
            time.sleep(1)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (output/'download-report.json').write_text(json.dumps({'prepared':len(manifest['players']),
        'skipped':skipped, 'api_calls':0},indent=2)+'\n',encoding='utf-8')
    print('Prepared '+str(len(manifest['players']))+' private portraits')


if __name__ == '__main__':
    main()
