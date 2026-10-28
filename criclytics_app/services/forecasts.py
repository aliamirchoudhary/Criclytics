"""Default-off local shadow inference; never collects or promotes a model."""
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
import time

from .reconciliation import Reconciler, StateLedger
from .json_io import read_json
from ..pipeline.events import checksum
from ..pipeline.artifacts import digest


class ForecastService:
    def __init__(self, source, ledger, model, model_sha, evaluation, evaluation_sha, clock=time.time, baselines=None, baselines_sha=None):
        from ..ml.baseline import load_model
        from ..paths import PACKAGE_ROOT, PROJECT_ROOT
        self.source, self.ledger = Path(source).resolve(), Path(ledger).resolve()
        for path in (self.source, self.ledger, Path(model).resolve(), Path(evaluation).resolve()):
            if any(path == public or path.is_relative_to(public) for public in
                   (PACKAGE_ROOT/'static', PROJECT_ROOT/'dist')):
                raise ValueError('Shadow artifacts must be private')
        if self.ledger in (self.source, self.source.with_suffix('.collector.sqlite3')):
            raise ValueError('Derived ledger must be separate from source and collector coordinator')
        if not evaluation_sha or digest(evaluation) != evaluation_sha:
            raise ValueError('Trusted evaluation hash required')
        self.model = load_model(model, model_sha)
        self.report = read_json(evaluation)
        features = self.report.get('feature_manifest', {})
        if (self.report.get('model_id') != model_sha or not self.model.get('dataset_id')
                or features.get('dataset_id') != self.model['dataset_id']
                or features.get('rows_sha256') != self.model.get('features_sha256')
                or not self.model.get('training_last_date') or not self.model.get('calibration_last_date')):
            raise ValueError('Model/evaluation/data provenance mismatch')
        self.model_id, self.clock = model_sha, clock
        self.baselines=None;self.baselines_sha=baselines_sha
        if baselines:
            baseline_path=Path(baselines).resolve()
            if any(baseline_path.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):raise ValueError('Baselines must be private')
            from ..ml.shadow_baselines import load
            self.baselines=load(baseline_path,baselines_sha,model_sha,self.model)
            self.protocol_sha=digest(PROJECT_ROOT/'docs/SHADOW_PROTOCOL.md')
            if self.baselines.get('protocol_sha256')!=self.protocol_sha:raise ValueError('Baseline/protocol mismatch')
        self.reconciler = Reconciler(self.source, clock=clock)
        self._lock = threading.RLock()
        self.inferences = 0
        self._ledger_initialized=False

    def open_ledger(self):
        ledger=StateLedger(self.ledger,initialize=not self._ledger_initialized)
        self._ledger_initialized=True
        return ledger

    @contextmanager
    def source_confirmation(self):
        """Serialize against collector reservations; pending raw commits abstain."""
        path = self.source.with_suffix('.collector.sqlite3')
        with closing(sqlite3.connect(path.as_uri()+'?mode=rw', uri=True, timeout=.25)) as db:
            db.execute('BEGIN IMMEDIATE')
            try: yield
            finally: db.rollback()

    def metadata(self):
        return {'model_id': self.model_id, 'dataset_id': self.model['dataset_id'], 'feature_schema': 1,
                'promoted': False, 'experimental': True, 'target_kind': 'next_attempt',
                'training_last_date': self.model['training_last_date'],
                'calibration_last_date': self.model['calibration_last_date'],
                'training_coverage': self.report['feature_manifest'].get('partitions'),
                'limitations': 'Local experimental shadow only; not validated for current coaching. Session-only priors; optional context excluded.',
                'attribution': 'Cricsheet JSON (ODC-BY-1.0); source observations are local manual/replay.'}

    def get_state(self, match_id):
        try: state = self.reconciler.get(match_id)
        except (sqlite3.Error, ValueError, OSError):
            state = {'available': False, 'forecast_allowed': False, 'blocked_reasons': ['source_unavailable_or_invalid'], 'state_id': None}
        reasons = list(state['blocked_reasons']); core = state.get('core')
        if core:
            scope = core['scope']; active = core['active_innings']
            if (scope['format'] != 'T20I' or scope['gender'] != 'male'
                    or scope['team_type'] != 'international' or scope.get('balls_per_over') != 6
                    or active not in (1, 2) or core['innings'][active-1]['super_over']):
                reasons.append('outside_model_scope')
            if not core['features']: reasons.append('missing_features')
        state['blocked_reasons'] = sorted(set(reasons))
        state['forecast_allowed'] = bool(core) and not reasons
        state['eligibility_valid_for_seconds'] = 0
        if state['forecast_allowed']:
            from .weather import utc
            announced = utc(core['next_context']['announced_at']).timestamp()
            state['eligibility_valid_for_seconds'] = max(0, min(15-(self.clock()-announced), 60-state['source_age_seconds']))
        return {'api_version': 1, **state, 'model': self.metadata()}

    def forecast(self, match_id):
        from ..ml.baseline import predict
        with self._lock:
            try:
                with self.source_confirmation():
                    state = self.get_state(match_id)
                    reasons = list(state['blocked_reasons'])
                    core = state.get('core')
                    if reasons or not core:
                        if core:
                            with closing(self.open_ledger()) as ledger:
                                now=datetime.fromtimestamp(self.clock(),timezone.utc).isoformat()
                                ledger.record(core,reasons,now=now);ledger.decision(core,reasons,now)
                        return {**state, 'forecast_allowed': False, 'blocked_reasons': sorted(set(reasons)), 'forecast': None}
                    with closing(self.open_ledger()) as ledger:
                        cached=ledger.connection.execute('SELECT f.forecast_id FROM issued_forecasts f JOIN current_state c ON c.state_id=f.state_id WHERE f.state_id=? AND f.model_id=?',
                                                         (checksum(core),self.model_id)).fetchone()
                        if cached:return {**state,'forecast':ledger.forecast(cached[0])}
                        sid = ledger.record(core)
                        ledger.decision(core,[],datetime.fromtimestamp(self.clock(),timezone.utc).isoformat())
                        old = ledger.connection.execute('SELECT forecast_id FROM issued_forecasts WHERE state_id=? AND model_id=?',
                                                        (sid, self.model_id)).fetchone()
                        if old:
                            return {**state, 'forecast': ledger.forecast(old[0])}
                        started = time.perf_counter()
                        distribution = predict(self.model, core['features'])
                        elapsed = (time.perf_counter()-started)*1000
                        # No unrelated worker can reserve a new source capture under this lock.
                        # The real ball can still start without a capture: this remains shadow-only.
                        issued_at = datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()
                        current = self.get_state(match_id)
                        if not current['forecast_allowed'] or current['state_id'] != sid:
                            return {**current, 'forecast_allowed': False, 'blocked_reasons': sorted(set(current['blocked_reasons']+['state_changed_during_inference'])), 'forecast': None}
                        content = {'schema_version': 1, 'match_id': match_id, 'target_event_id': core['target_event_id'],
                                   'state_id': sid, 'source_cutoff': core['source_cutoff'],
                                   'source_revision_hash': core['source_revision_hash'], 'mode': core['mode'],
                                   'feature_hash': checksum(core['features']), 'feature_schema': 1,
                                   'model_id': self.model_id, 'dataset_id': self.model['dataset_id'],
                                   'distribution': distribution, 'unknown_mass': distribution['OTHER'],
                                   'semantics': 'Joint next attempt including illegal deliveries. OTHER has unknown runs/dismissals; it is not zero-risk.',
                                   'experimental': True, 'promoted': False, 'model': self.metadata()}
                        if self.baselines:
                            from ..ml.shadow_baselines import predict as baseline_predict
                            content['baselines']=baseline_predict(self.baselines,core['features'])
                            content['baseline_artifact_sha256']=self.baselines_sha
                            content['protocol_sha256']=self.protocol_sha
                        issued = ledger.issue(content, issued_at)
                        self.inferences += 1
                        return {**current, 'forecast': issued, 'inference_ms': round(elapsed, 4)}
            except sqlite3.OperationalError:
                return {'api_version': 1, 'available': False, 'forecast_allowed': False,
                        'blocked_reasons': ['source_or_ledger_unavailable'], 'forecast': None, 'model': self.metadata()}

    def history(self, match_id, limit=50):
        if not 1 <= limit <= 200: raise ValueError('History limit must be1..200')
        if not self.ledger.exists(): return []
        # Readers must not create a database or run migrations.
        with closing(sqlite3.connect(self.ledger.as_uri()+'?mode=ro', uri=True, timeout=.25)) as db:
            rows = db.execute('SELECT forecast_id,issued_at,payload,replaces FROM issued_forecasts WHERE match_id=? ORDER BY rowid DESC LIMIT ?',
                              (match_id, limit)).fetchall()
        return [{'forecast_id': row[0], 'issued_at': row[1], 'content': json.loads(row[2]), 'replaces_forecast_id': row[3]} for row in rows]


def initialize(app):
    app.extensions['forecast_service'] = None
    if not app.config['EXPERIMENTAL_FORECASTS']: return
    app.extensions['forecast_service'] = ForecastService(app.config['WORKSPACE_SOURCE'], app.config['WORKSPACE_LEDGER'],
        app.config['FORECAST_MODEL'], app.config['FORECAST_MODEL_SHA256'],
        app.config['FORECAST_EVALUATION'], app.config['FORECAST_EVALUATION_SHA256'],
        baselines=app.config['FORECAST_BASELINES'] or None,baselines_sha=app.config['FORECAST_BASELINES_SHA256'] or None)
