"""Trusted contextual what-if inference, distinct from live issued forecasts."""
from datetime import date
import json
import math
from pathlib import Path
import re

import numpy as np

from ..ml.contextual import FAMILIES, components, calibrated, event_bounds, keys
from ..pipeline.artifacts import digest
from ..pipeline.scoring import DISMISSALS, NOT_DISMISSED


class ScenarioModel:
    def __init__(self, path, expected, evaluation, evaluation_sha):
        from ..paths import PACKAGE_ROOT, PROJECT_ROOT
        path, evaluation = Path(path).resolve(), Path(evaluation).resolve()
        for value in (path,evaluation):
            if any(value == root or value.is_relative_to(root) for root in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):
                raise ValueError('Full model/evaluation artifacts must remain private')
        if path.stat().st_size > 64*1024*1024 or not expected or digest(path) != expected:
            raise ValueError('Untrusted or oversized scenario model')
        if evaluation.stat().st_size > 2*1024*1024 or not evaluation_sha or digest(evaluation) != evaluation_sha:
            raise ValueError('Untrusted scenario evaluation')
        model = json.loads(path.read_text(encoding='utf-8'))
        report = json.loads(evaluation.read_text(encoding='utf-8'))
        if (model.get('artifact_schema') != 'contextual-v1' or model.get('promoted') is not False
                or model.get('target_kind') != 'next_attempt' or report.get('model_sha256') != expected
                or report.get('corpus_sha256') != model.get('corpus_sha256')
                or report.get('protocol_sha256') != model.get('protocol_sha256')):
            raise ValueError('Scenario artifact/evaluation contract mismatch')
        if model.get('scope') != {'format':'T20I','gender':'male','team_type':'international','balls_per_over':6}:
            raise ValueError('Unsupported scenario scope')
        labels = model['labels']
        if not 3 <= len(labels) <= 64 or labels[0] != 'OTHER' or len(set(labels)) != len(labels):
            raise ValueError('Invalid joint vocabulary')
        for value in labels[1:]:
            joint = json.loads(value)
            if set(joint) != {'batter_runs','extras','total_runs','dismissals','legal'} or set(joint['extras']) != {'wides','noballs','byes','legbyes','penalty'}:
                raise ValueError('Invalid joint label')
            if any(type(n) is not int or n < 0 for n in (joint['batter_runs'],joint['total_runs'],*joint['extras'].values())):
                raise ValueError('Invalid joint counts')
            if joint['total_runs'] != joint['batter_runs']+sum(joint['extras'].values()):
                raise ValueError('Incoherent joint runs')
            if type(joint['legal']) is not bool or joint['legal'] == bool(joint['extras']['wides'] or joint['extras']['noballs']):
                raise ValueError('Incoherent delivery legality')
            if any(w not in DISMISSALS-NOT_DISMISSED for w in joint['dismissals']):
                raise ValueError('Invalid dismissal')
        def counts(values):
            if len(values) != len(labels) or any(type(v) is not int or v < 0 for v in values):
                raise ValueError('Invalid model counts')
        if set(model['counts']) != set(FAMILIES[:7]):
            raise ValueError('Invalid component schema')
        for family in FAMILIES[:7]:
            if len(model['counts'][family]) > 200000:
                raise ValueError('Unbounded context table')
            for values in model['counts'][family].values():
                counts(values)
        if sum(model['counts']['global']['all']) == 0:
            raise ValueError('Missing training sample')
        weights = np.asarray(model['weights'],dtype=float)
        if weights.shape != (9,) or not np.isfinite(weights).all() or (weights<0).any() or not np.isclose(weights.sum(),1):
            raise ValueError('Invalid mixture weights')
        if not math.isfinite(model['temperature']) or not .5 <= model['temperature'] <= 3:
            raise ValueError('Invalid calibration')
        if not model['first_date'] <= model['training_last_date'] <= model['calibration_last_date'] <= model['data_asof']:
            raise ValueError('Invalid temporal provenance')
        date.fromisoformat(model['data_asof'])
        for role in ('batter','bowler'):
            for row in model['forms'][role].values():
                counts(row['counts'])
                if row['last_date'] > model['data_asof'] or not 1 <= row['matches'] <= 5:
                    raise ValueError('Invalid recent history')
        self.model, self.report, self.identity, self.evaluation_sha = model, report, expected, evaluation_sha

    def catalog(self):
        return {'available':True, 'experimental':True, 'promoted':False,
                'model_id':self.identity, 'scope':self.model['scope'], 'data_asof':self.model['data_asof'],
                'training_last_date':self.model['training_last_date'], 'venues':self.model['venues'],
                'teams':self.model['teams'], 'metrics':self.report['metrics'],
                'matches':self.report['matches'], 'loss_delta':self.report['loss_delta'],
                'evaluation_sha256':self.evaluation_sha,
                'test_period':self.report['partition_first_dates']['test']+' to '+self.report['date_range'][1],
                'unsupported_context':['weather/surface effects','crowd/booing','psychological pressure',
                                       'politics/captaincy pressure','fielding-incident causal effects'],
                'availability_limit':self.report['availability']}

    def predict(self, batter, bowler, venue, teams=(), innings=1, phase=0, as_of=None):
        model = self.model
        for identity in (batter,bowler):
            if not re.fullmatch(r'player:cricsheet:[a-f0-9]{8}',identity):
                raise ValueError('Choose a stable Cricsheet player identity')
        if batter == bowler:
            raise ValueError('Choose different batter and bowler identities')
        if venue not in model['venues'] or innings not in (1,2) or phase not in (0,1,2):
            raise ValueError('Choose a supported venue/innings/phase')
        if len(teams) not in (0,2) or len(set(teams)) != len(teams) or any(t not in model['teams'] for t in teams):
            raise ValueError('Choose two different observed teams, or omit both')
        as_of = as_of or date.today().isoformat()
        date.fromisoformat(as_of)
        if as_of < model['data_asof']:
            raise ValueError('Scenario date predates the available form snapshot; no future-data lookup allowed')
        context = keys(batter,bowler,venue,teams,innings,phase)
        form, details = [], {}
        for role, identity in (('batter',batter),('bowler',bowler)):
            row = model['forms'][role].get(identity)
            form.append(row['counts'] if row else None)
            details[role] = {'matches':row['matches'] if row else 0, 'last_observed_date':row['last_date'] if row else None,
                             'age_days':(date.fromisoformat(as_of)-date.fromisoformat(row['last_date'])).days if row else None}
        vectors, samples = components(model,context,form)
        probabilities = calibrated(np.asarray(model['weights'])@vectors,model['temperature'])
        if not np.isfinite(probabilities).all() or not np.isclose(probabilities.sum(),1):
            raise ValueError('Invalid probability distribution')
        return {'available':True,'kind':'hypothetical_next_attempt','experimental':True,'promoted':False,
                'model_id':self.identity,'scope':model['scope'],'as_of':as_of,'data_asof':model['data_asof'],
                'training_last_date':model['training_last_date'],'context':{'batter':batter,'bowler':bowler,'venue':venue,
                'teams':list(teams),'innings':innings,'phase':phase},
                'distribution':dict(zip(model['labels'],map(float,probabilities))),
                'unknown_mass':float(probabilities[0]), 'events':event_bounds(model['labels'],probabilities),
                'component_samples':dict(zip(FAMILIES,samples)), 'mixture_weights':dict(zip(FAMILIES,model['weights'])),
                'recent_form':details,'cold_start':samples[2]==0 or samples[3]==0,
                'unsupported_context':self.catalog()['unsupported_context'],
                'limitations':['Hypothetical historical-data scenario, not a current live forecast.',
                               'Recent-form age and sample gaps matter; no mental state is inferred.',
                               'Events may overlap. OTHER gives probability bounds, not exact missing outcomes.']}


def initialize(app):
    app.extensions['scenario_model'] = None
    if app.config['SCENARIO_MODEL']:
        app.extensions['scenario_model'] = ScenarioModel(app.config['SCENARIO_MODEL'],app.config['SCENARIO_MODEL_SHA256'],
            app.config['SCENARIO_EVALUATION'],app.config['SCENARIO_EVALUATION_SHA256'])
