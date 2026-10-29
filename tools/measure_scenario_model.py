"""Measure trusted local scenario inference without HTTP or external calls."""
import argparse
import json
from pathlib import Path
import statistics
import time

from criclytics_app.pipeline.artifacts import digest
from criclytics_app.services.scenarios import ScenarioModel
from tools.measure_repository import working_set


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--repeat-dir', type=Path, required=True)
    parser.add_argument('--training-memory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    model, evaluation = args.artifact_dir/'model.json', args.artifact_dir/'evaluation.json'
    before = working_set()
    started = time.perf_counter()
    service = ScenarioModel(model, digest(model), evaluation, digest(evaluation))
    load_ms = (time.perf_counter()-started)*1000
    after = working_set()
    batter = next(iter(service.model['forms']['batter']))
    bowler = next(p for p in service.model['forms']['bowler'] if p != batter)
    samples = []
    for _ in range(1000):
        started = time.perf_counter()
        result = service.predict(batter, bowler, service.model['venues'][0])
        samples.append((time.perf_counter()-started)*1000)
        assert abs(sum(result['distribution'].values())-1) < 1e-10
    report = {'model_bytes':model.stat().st_size, 'load_ms':round(load_ms,3),
              'working_set_before_bytes':before, 'working_set_after_load_bytes':after,
              'inferences':len(samples), 'inference_p50_ms':round(statistics.median(samples),3),
              'inference_p95_ms':round(sorted(samples)[949],3),
              'training':json.loads(args.training_memory.read_text(encoding='utf-8-sig')),
              'repeat_model_identical':digest(model)==digest(args.repeat_dir/'model.json'),
              'repeat_metrics_identical':json.loads(evaluation.read_text())['metrics']==
                  json.loads((args.repeat_dir/'evaluation.json').read_text())['metrics'],
              'scope':'Local Windows CPU; single-process inference, not hosted capacity or latency.'}
    assert report['repeat_model_identical'] and report['repeat_metrics_identical']
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
