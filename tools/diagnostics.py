"""Offline, bounded resource diagnostic. Never fetch providers or expose paths/secrets."""
import argparse
import json
from pathlib import Path
import tempfile
import time
from criclytics_app import create_app
from criclytics_app.services.diagnostics import readiness
from tools.measure_repository import working_set


def report(processed=None,samples=20):
    if not 1<=samples<=50: raise ValueError('samples must be between1 and50')
    with tempfile.TemporaryDirectory() as live:
        config={'LIVE_DIR':live,'LIVE_FETCH_ENABLED':False,'REDIS_URL':''}
        if processed:config['PROCESSED_DIR']=str(processed)
        app=create_app(config)
        results=[]
        with app.app_context(): ready=readiness(app)
        with app.test_client() as client:
            for _ in range(samples):
                start=time.perf_counter();response=client.get('/api/matches?status=completed&limit=20')
                results.append({'milliseconds':round((time.perf_counter()-start)*1000,3),'bytes':len(response.data),'status':response.status_code})
        return {'readiness':ready,'telemetry':app.extensions['diagnostics'].snapshot(),'samples':results,
                'resident_bytes':working_set(),'limitations':'Single offline process, local disk and OS cache; not hosted capacity or latency guarantees. No provider quota reserved/consumed.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--processed-dir',type=Path)
    parser.add_argument('--samples',type=int,default=20)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args(); result=report(args.processed_dir,args.samples)
    encoded=json.dumps(result,indent=2)+'\n'
    if args.output:args.output.write_text(encoded,encoding='utf-8')
    else:print(encoded)
    return 0 if result['readiness']['ready'] and all(r['status']==200 for r in result['samples']) else 1


if __name__=='__main__':raise SystemExit(main())
