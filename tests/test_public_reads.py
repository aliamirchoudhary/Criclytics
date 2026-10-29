from concurrent.futures import ThreadPoolExecutor
import tempfile
from threading import Barrier, Lock
import time
import unittest

from flask import jsonify

from criclytics_app import create_app
from criclytics_app.services.public_reads import PublicReads


class PublicReadTests(unittest.TestCase):
    def test_concurrent_reads_compute_once_and_preserve_request_headers(self):
        with tempfile.TemporaryDirectory() as folder:
            app = create_app({'TESTING':True,'PUBLIC_READ_CACHE_ENABLED':True,
                'PROCESSED_DIR':folder,'LIVE_DIR':folder,'LIVE_FETCH_ENABLED':False,'REDIS_URL':'',
                'CORS_ORIGINS':['https://one.example','https://two.example']})
            calls, lock, ready = [], Lock(), Barrier(8)
            def listing():
                with lock: calls.append(1)
                time.sleep(.1)
                return jsonify(data=[{'name':'Authored player'}])
            app.view_functions['api.get_players'] = listing
            def read(_):
                ready.wait(timeout=3)
                with app.test_client() as client:
                    return client.get('/api/players?limit=2',headers={'Origin':'https://one.example'})
            with ThreadPoolExecutor(max_workers=8) as pool:
                responses = list(pool.map(read,range(8)))
            self.assertEqual(len(calls),1)
            self.assertTrue(all(r.status_code==200 for r in responses))
            self.assertEqual(len({r.headers['X-Request-ID'] for r in responses}),8)
            self.assertTrue(all(r.headers['Access-Control-Allow-Origin']=='https://one.example' for r in responses))
            with app.test_client() as client:
                cached = client.get('/api/players?limit=2',headers={'Origin':'https://two.example'})
                self.assertEqual(cached.headers['Access-Control-Allow-Origin'],'https://two.example')
                conditional = client.get('/api/players?limit=2',headers={'If-None-Match':cached.headers['ETag']})
                self.assertEqual(conditional.status_code,304)
                self.assertEqual(conditional.data,b'')
                self.assertEqual(client.get('/api/players?limit=2&limit=3').status_code,400)
                self.assertEqual(client.get('/api/players?'+('&'.join(f'k{i}=v' for i in range(21)))).status_code,400)
                self.assertEqual(client.get('/api/players?'+('long=v&'*600)).status_code,400)
                client.get('/api/players?limit=2',headers={'Authorization':'Bearer authored'})
                self.assertEqual(len(calls),2)
                for url in ('/api/v1/scenarios','/api/v1/workspaces'):
                    self.assertIn('no-store',client.get(url).headers.get('Cache-Control',''))
            self.assertEqual(app.extensions['public_reads'].snapshot()['in_flight'],0)

    def test_ttl_eviction_size_busy_and_failed_owner_cleanup(self):
        clock = [0]
        cache = PublicReads(ttl=2,maximum=2,budget=6,response_limit=4,flights=1,wait=.001,clock=lambda:clock[0])
        _, event, _ = cache.acquire('a')
        self.assertTrue(cache.acquire('other')[2])
        cache.release('a',event,b'1234')
        self.assertEqual(cache.acquire('a')[0].body,b'1234')
        _, event, _ = cache.acquire('b'); cache.release('b',event,b'1234')
        self.assertEqual(cache.snapshot()['bytes'],4)
        self.assertEqual(cache.snapshot()['entries'],1)
        clock[0] = 3
        entry,event,_ = cache.acquire('b'); self.assertIsNone(entry)
        cache.release('b',event,b'oversized')
        self.assertEqual(cache.snapshot()['entries'],0)
        _,event,_ = cache.acquire('error');cache.release('error',event)
        self.assertEqual(cache.snapshot()['in_flight'],0)
        _,event,_ = cache.acquire('error');cache.release('error',event,b'{}')
        self.assertEqual(cache.snapshot()['entries'],1)
