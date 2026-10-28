"""Local experimental model latency/readers evidence, not prospective scoring."""
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import time
import numpy as np
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.pipeline.events import initial_state, apply_event
from criclytics_app.services.forecasts import ForecastService
from tests.test_reconciliation import setup_data, next_context, observation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,default=PROJECT_ROOT/'docs/audit/forecast-service-2026-10-28.json')
    args=parser.parse_args()
    model = PROJECT_ROOT/'build/baseline-v1-first/model.json'
    evaluation = PROJECT_ROOT/'build/baseline-v1-first/evaluation.json'
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); now = datetime(2026,10,28,12,tzinfo=timezone.utc).timestamp()
        meta, one, _ = setup_data(); meta['dates'] = ['2026-10-28']
        collector = LocalCollector(root/'source.sqlite3', enabled=True, clock=lambda:now)
        try:
            score = apply_event(initial_state(meta,1),one)
            collector.ingest(meta,observation(meta,'one',[one],next_context(score,2)))
            service = ForecastService(root/'source.sqlite3',root/'ledger.sqlite3',model,digest(model),evaluation,digest(evaluation),clock=lambda:now)
            start = time.perf_counter(); first = service.forecast(meta['match_id']); first_ms=(time.perf_counter()-start)*1000
            assert first['forecast_allowed'], first
            def read(_):
                start=time.perf_counter();value=service.forecast(meta['match_id'])
                assert value['forecast']==first['forecast']
                return (time.perf_counter()-start)*1000
            with ThreadPoolExecutor(max_workers=4) as workers: samples=list(workers.map(read,range(100)))
            assert service.inferences==1
            assert collector.guard.execute('SELECT COUNT(*) FROM inputs').fetchone()[0]==1
            from tools.measure_repository import working_set
            result={'model_id':digest(model),'evaluation_sha256':digest(evaluation),'promoted':False,
                    'first_end_to_end_ms':first_ms,'single_inference_ms':first['inference_ms'],
                    'readers':100,'threads':4,'reader_ms':{'p50':float(np.percentile(samples,50)),'p95':float(np.percentile(samples,95)),'max':max(samples)},
                    'inferences':service.inferences,'collector_inputs':1,'resident_bytes':working_set(),
                    'target':'Local warm single inference below10ms; bounded4-reader p95 below100ms. No hosted SLA.',
                    'parity':'Uses the T026 shared feature core; actual250historical before-attempt parity recorded separately.',
                    'limitations':'One authored manual session with real experimental weights. No prospective performance, actual human latency or model promotion.'}
            assert first['inference_ms']<10 and np.percentile(samples,95)<100,result
            args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(result))
        finally:collector.close()


if __name__=='__main__':main()
