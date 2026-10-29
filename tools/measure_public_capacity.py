"""Local HTTP capacity check; never send a load test to a hosted service."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from pathlib import Path
import statistics
from threading import BoundedSemaphore, Thread
import time
from unittest.mock import patch
from urllib.request import urlopen

from werkzeug.serving import make_server

from criclytics_app import create_app
from tools.measure_repository import working_set


class TwoSlots:
    def __init__(self, app):
        self.app, self.slots = app, BoundedSemaphore(2)

    def __call__(self, environ, start_response):
        # Flask responses are buffered; bound application execution to the
        # deployed two-thread configuration. The development HTTP transport
        # still has its own threads and is not a Gunicorn benchmark.
        with self.slots:
            return list(self.app(environ,start_response))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed-dir',type=Path,required=True)
    parser.add_argument('--identity-registry',type=Path,required=True)
    parser.add_argument('--player-store',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    app = create_app({'PROCESSED_DIR':args.processed_dir,'DATASET_STORE':'',
        'IDENTITY_REGISTRY':args.identity_registry,'IDENTITY_PLAYER_STORE':args.player_store,
        'LIVE_DIR':'build/t035-capacity-live','LIVE_FETCH_ENABLED':False,'REDIS_URL':'',
        'SCENARIO_MODEL':'','EXPERIMENTAL_FORECASTS':False,'SCOUTING_SAMPLE':''})
    app.logger.setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    server = make_server('127.0.0.1',0,TwoSlots(app),threaded=True)
    Thread(target=server.serve_forever,daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    paths = ['/api/players?format=T20I&limit=24','/api/teams?format=T20I',
             '/api/venues?format=T20I','/api/rankings?format=T20I&type=batting&limit=30']
    before, batches = working_set(), []

    def read(path):
        started = time.perf_counter()
        with urlopen(base+path,timeout=20) as response:
            payload = response.read()
            assert response.status == 200 and json.loads(payload) is not None
            return (time.perf_counter()-started)*1000,len(payload)

    try:
        # urllib local requests are allowed; any Requests-based provider attempt
        # fails this check instead of silently contacting an external service.
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Provider call during public reads')) as network:
            for mode in ('cold','warm'):
                started = time.perf_counter()
                with ThreadPoolExecutor(max_workers=100) as pool:
                    rows = list(pool.map(read,[paths[i%len(paths)] for i in range(100)]))
                elapsed = time.perf_counter()-started
                durations = sorted(row[0] for row in rows)
                batches.append({'mode':mode,'requests':len(rows),'concurrency':100,
                    'elapsed_seconds':round(elapsed,3),'requests_per_second':round(len(rows)/elapsed,2),
                    'p50_ms':round(statistics.median(durations),2),'p95_ms':round(durations[94],2),
                    'max_response_bytes':max(row[1] for row in rows),'failures':0})
            assert network.call_count == 0
            report = {'batches':batches,'provider_calls':network.call_count,
                'working_set_before_bytes':before,'working_set_after_bytes':working_set(),
                'cache':app.extensions['public_reads'].snapshot(),
                'limits':'Local Windows HTTP, 2 application slots,100 client threads; not Gunicorn/free-host/CDN capacity or an SLA. OS/disk caches not flushed. No live/scenario/private endpoint load.'}
    finally:
        server.shutdown()
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':main()
