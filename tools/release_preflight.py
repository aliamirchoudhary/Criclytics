"""Independent offline artifact/restore preparation. Never deploys or approves release."""
from contextlib import closing,redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.web.routes import PAGES
from criclytics_app.pipeline.artifacts import digest,promote,selected
from criclytics_app.pipeline.rebuild import rebuild
from criclytics_app.pipeline.events import initial_state,apply_event
from criclytics_app.integrations.collector import LocalCollector
from criclytics_app.services.forecasts import ForecastService
from criclytics_app.services.reconciliation import Reconciler
from scripts.build_frontend import build
from scripts.stage_backend import stage
from tests.test_reconciliation import setup_data,observation,next_context,NOW


def backup(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as old,closing(sqlite3.connect(target)) as new:
        old.backup(new)
        assert new.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def main():
    with tempfile.TemporaryDirectory() as directory,patch('requests.get',side_effect=AssertionError('Network is forbidden in offline release preparation')):
        recorded=json.loads((PROJECT_ROOT/'build/data-v3-manifest-final/manifest.json').read_text(encoding='utf-8'))['original_artifacts']
        assert recorded and all(digest(PROJECT_ROOT/'data/processed'/name)==checksum for name,checksum in recorded.items())
        root=Path(directory);frontend=build(root/'frontend','https://backend.example.invalid');backend=stage(root/'backend')
        assert {p.name for p in frontend.glob('*.html')}==PAGES
        forbidden={'.env','.git','raw','processed','build','node_modules'}
        for artifact in (frontend,backend):
            for path in artifact.rglob('*'):
                assert not (set(path.relative_to(artifact).parts)&forbidden),path.name
                assert path.suffix not in ('.pkl','.pickle','.sqlite3','.csv'),path.name
        assert (frontend/'scouting.html').is_file() and (frontend/'workspace.html').is_file()
        app=create_app({'PROCESSED_DIR':PROJECT_ROOT/'build/data-v3-manifest-final',
                        'IDENTITY_REGISTRY':PROJECT_ROOT/'build/identities-v1-final.json',
                        'IDENTITY_PLAYER_STORE':PROJECT_ROOT/'build/player-ids-v1-final',
                        'SCOUTING_SAMPLE':PROJECT_ROOT/'build/scouting-delivery-v1.json',
                        'LIVE_DIR':root/'live','REDIS_URL':'','LIVE_FETCH_ENABLED':False,'EXPERIMENTAL_FORECASTS':False})
        client=app.test_client();responses={}
        for url in ('/api/ready','/api/coverage','/api/players?limit=5','/api/players/SC%20Cook',
                    '/api/v1/scouting?player=SC%20Cook&format=Test','/api/v1/workspaces/match:manual:none/forecast','/api/predict/status'):
            response=client.get(url);assert response.status_code==200,(url,response.status_code)
            responses[url]={'status':response.status_code,'bytes':len(response.data)}
            if 'workspaces' in url:assert response.json['forecast'] is None
            if url=='/api/predict/status':assert response.json['available'] is False
        for url in ('/.env','/.git/HEAD','/data/raw/source.json','/build/baseline-v1-first/model.json',
                    '/docs/SESSION_PROGRESS.md','/static/../services/legacy.py'):
            assert client.get(url).status_code==404
        for page in PAGES:
            response=client.get('/'+page)
            assert response.status_code==200
            assert "script-src 'self'" in response.headers['Content-Security-Policy']
            response.close()

        # Dedicated authored session. Kill/pause the producer before cross-database backups.
        source=root/'original/source.sqlite3';ledger=root/'original/ledger.sqlite3';meta,one,_=setup_data()
        collector=LocalCollector(source,enabled=True,clock=lambda:NOW)
        model=PROJECT_ROOT/'build/baseline-v1-first/model.json';evaluation=PROJECT_ROOT/'build/baseline-v1-first/evaluation.json'
        try:
            collector.ingest(meta,observation(meta,'one',[one],next_context(apply_event(initial_state(meta,1),one),2)))
            service=ForecastService(source,ledger,model,digest(model),evaluation,digest(evaluation),clock=lambda:NOW)
            issued=service.forecast(meta['match_id'])['forecast'];assert issued
            collector.kill(True)
            original={p:digest(p) for p in (source,ledger)}
            restored=root/'restored/source.sqlite3';restored_ledger=root/'restored/ledger.sqlite3'
            backup(source,restored);backup(source.with_suffix('.collector.sqlite3'),restored.with_suffix('.collector.sqlite3'));backup(ledger,restored_ledger)
            review=ForecastService(restored,restored_ledger,model,digest(model),evaluation,digest(evaluation),clock=lambda:NOW)
            restored_state=review.get_state(meta['match_id'])
            assert not restored_state['forecast_allowed'] and 'killed' in restored_state['blocked_reasons']
            assert review.history(meta['match_id'])==[issued]
            assert all(digest(path)==checksum for path,checksum in original.items())
        finally:collector.close()

        # Retained JSON version rollback, using only authored golden fixtures.
        pack=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))
        candidates=[]
        with redirect_stdout(io.StringIO()):
            for index in (1,2):
                raw=root/('raw'+str(index))/'tests_male_json';raw.mkdir(parents=True)
                fixture=deepcopy(pack['fixtures'][0]['match']);fixture['info']['dates']=['2020-01-0'+str(index)]
                (raw/'fixture.json').write_text(json.dumps(fixture),encoding='utf-8');candidate=root/('dataset'+str(index))
                rebuild(raw.parent,candidate);candidates.append(candidate)
            store=root/'dataset-store';a=promote(candidates[0],store,digest(candidates[0]/'manifest.json'))
            b=promote(candidates[1],store,digest(candidates[1]/'manifest.json'));assert a!=b and selected(store)==b
            promote(a,store,digest(a/'manifest.json'));assert selected(store)==a and b.is_dir()
        audit=json.loads((PROJECT_ROOT/'build/t031-dependency-audit.json').read_text(encoding='utf-8'))
        vulnerabilities=sum(len(row.get('vulns',[])) for row in audit['dependencies']);assert vulnerabilities==0
        result={'release_decision':'BLOCKED','public_pages':len(PAGES),'clean_frontend_allowlist':True,'clean_backend_allowlist':True,
                'original_processed_hashes_verified':len(recorded),
                'offline_api_smoke':responses,'public_private_paths_denied':True,'script_csp_enforced':True,
                'dependency_audit':{'packages':len(audit['dependencies']),'known_advisories':vulnerabilities,'source':'pip-audit resolved pinned requirements; not proof of absent application vulnerabilities'},
                'authored_restore_drill':{'sqlite_integrity':True,'source_and_collector_coordinator_and_ledger':True,'kill_retained':True,'issued_payload_unchanged':True,'original_source_ledger_hashes_unchanged':True,
                                         'two_immutable_json_versions_and_rollback':True,'previous_version_retained':True},
                'actual_coach_participants':0,'actual_prospective_matches':0,'hosted_restore_verified':False,'deployment':None,
                'blockers':['T001 credential rotation/production containment','T013 remote branch/CI/host release verification','T029 real coach feedback','T030 prospective cohort/timing/metrics','Git publication/integration approval'],
                'limitations':'Offline local fixtures/candidates only. Network GET blocked during smoke/drill. No production resource, original dataset, credential, Git remote or deployment changed.'}
        (PROJECT_ROOT/'docs/audit/release-preflight-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'release_decision':'BLOCKED','pages':len(PAGES),'known_advisories':vulnerabilities,'restore_drill':result['authored_restore_drill']}))


if __name__=='__main__':main()
