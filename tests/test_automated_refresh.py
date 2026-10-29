from copy import deepcopy
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from criclytics_app.pipeline.refresh import ARCHIVES,extract,refresh
from criclytics_app.pipeline.artifacts import digest,validate


def archive(items):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for name,value in items:z.writestr(name,value)
    return output.getvalue()


class Response:
    def __init__(self,body=b'',status=200,headers=None):
        self.content,self.status_code,self.headers=body,status,headers or {}
        self.text=body.decode('utf-8',errors='replace')
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,size):
        for start in range(0,len(self.content),size):yield self.content[start:start+size]


class Session:
    def __init__(self,sources):self.sources=sources;self.headers={};self.calls=[]
    def close(self):pass
    def get(self,url,headers=None,**kwargs):
        self.calls.append((url,headers))
        if url.endswith('robots.txt'):return Response(b'User-agent: *\nAllow: /downloads/\nDisallow: /data/')
        key=url.rsplit('/',1)[-1][:-4]
        body,etag=self.sources[key]
        if headers and headers.get('If-None-Match')==etag:return Response(status=304)
        return Response(body,headers={'ETag':etag,'Content-Length':str(len(body))})


def sources():
    pack=json.loads(Path('tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))
    fixture=pack['fixtures'][0]['match']
    output={}
    for index,(folder,fmt) in enumerate(ARCHIVES.items(),1):
        raw=deepcopy(fixture)
        raw['info'].update(gender='male',team_type='international',match_type='T20' if fmt=='T20I' else fmt)
        output[folder]=(archive([(f'{index}01.json',json.dumps(raw)),(f'{index}02.json',json.dumps(raw))]),'"initial"')
    return output


class RefreshTests(unittest.TestCase):
    def test_authoritative_conditional_snapshot_and_failure_preserve_last_good(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'store';data=sources();clock=[1800000000]
            first=refresh(root,Session(data),lambda:clock[0])
            self.assertEqual(first['accepted_matches'],6)
            self.assertEqual(validate(root/first['candidate_path'])['dataset_id'],first['candidate_id'])
            no_calls=Session(data)
            self.assertEqual(refresh(root,no_calls,lambda:clock[0])['status'],'not_due')
            self.assertEqual(no_calls.calls,[])
            clock[0]+=86400
            same=refresh(root,Session(data),lambda:clock[0])
            self.assertEqual(same['status'],'unchanged')
            self.assertEqual(same['sources']['t20s_male_json']['http_status'],304)
            self.assertEqual(same['sources']['t20s_male_json']['received_at'],first['sources']['t20s_male_json']['received_at'])
            # A corrupt retained ZIP must trigger an unconditional repair, not304.
            path=root/'bronze'/(same['sources']['t20s_male_json']['sha256']+'.zip')
            path.write_bytes(b'corrupt')
            clock[0]+=86400
            repaired=refresh(root,Session(data),lambda:clock[0])
            self.assertEqual(repaired['sources']['t20s_male_json']['http_status'],200)
            self.assertEqual(repaired['candidate_id'],first['candidate_id'])
            self.assertEqual(len(list((root/'quarantine').glob('*.zip'))),1)
            with zipfile.ZipFile(io.BytesIO(data['t20s_male_json'][0])) as z:
                retained=z.read('301.json')
            data['t20s_male_json']=(archive([('301.json',retained)]),'"revised"')
            clock[0]+=86400
            removed=refresh(root,Session(data),lambda:clock[0])
            self.assertEqual(removed['accepted_matches'],5)
            self.assertEqual(removed['changes']['withdrawn'],['t20s_male_json/302.json'])
            checksum=digest(root/'latest.json')
            data['t20s_male_json']=(archive([('301.json','not json')]),'"invalid"')
            clock[0]+=86400
            with self.assertRaises(ValueError):refresh(root,Session(data),lambda:clock[0])
            self.assertEqual(digest(root/'latest.json'),checksum)
            self.assertEqual(validate(root/removed['candidate_path'])['dataset_id'],removed['candidate_id'])

    def test_untrusted_archives_and_public_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            dangerous=[archive([('../outside.json','{}')]),archive([('/outside.json','{}')]),
                       archive([('C:\\outside.json','{}')]),archive([('1.json','{}')]),
                       archive([('README.txt','empty')])]
            link=zipfile.ZipInfo('1.json');link.create_system=3;link.external_attr=(stat.S_IFLNK|0o777)<<16
            dangerous.append(archive([(link,'target')]))
            for index,body in enumerate(dangerous):
                path=root/f'{index}.zip';path.write_bytes(body)
                with self.assertRaises((ValueError,KeyError)):
                    extract(path,root/f'output{index}','t20s_male_json')
            with self.assertWarns(UserWarning):
                duplicate=archive([('README.txt','a'),('README.txt','b')])
            path=root/'duplicate.zip';path.write_bytes(duplicate)
            with self.assertRaises(ValueError):extract(path,root/'duplicate','t20s_male_json')
            valid=root/'large.zip';valid.write_bytes(sources()['t20s_male_json'][0])
            with patch('criclytics_app.pipeline.refresh.MAX_EXPANDED',10):
                with self.assertRaises(ValueError):extract(valid,root/'large','t20s_male_json')
            with self.assertRaises(ValueError):refresh(Path('criclytics_app/static/forbidden-refresh'),Session(sources()))

    def test_provider_stop_and_other_worker_lease_are_respected(self):
        import sqlite3
        from contextlib import closing
        class Denied(Session):
            def get(self,url,**kwargs):
                if url.endswith('robots.txt'):return super().get(url,**kwargs)
                self.calls.append((url,kwargs))
                return Response(status=429)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'store';client=Denied(sources())
            with self.assertRaises(ValueError):refresh(root,client,lambda:1800000000)
            self.assertEqual(len(client.calls),2)  # robots + one source, no retries
            self.assertFalse((root/'latest.json').exists())
            with closing(sqlite3.connect(root/'jobs.sqlite3')) as db,db:
                db.execute("INSERT INTO lease VALUES(1,'other-worker',1800001000)")
            waiting=Session(sources())
            with self.assertRaises(ValueError):refresh(root,waiting,lambda:1800000000)
            self.assertEqual(waiting.calls,[])
            with closing(sqlite3.connect(root/'jobs.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT owner FROM lease').fetchone()[0],'other-worker')
