"""Deterministic authored-fixture annotation replay; no real match incident claim."""
import json
from pathlib import Path
import tempfile
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.services.match_context import ContextLedger
from criclytics_app.services.annotations import annotation_context


def main():
    fixture=json.loads((PROJECT_ROOT/'tests/fixtures/annotation_example.json').read_text())
    with tempfile.TemporaryDirectory() as directory:
        ledger=ContextLedger(Path(directory)/'annotations.sqlite3')
        try:
            for record in reversed(fixture['records']):ledger.add(record)
            for record in fixture['records']:ledger.add(record)
            before=annotation_context(ledger.eligible('match:fixture','2020-01-01T10:00:01Z'),'match:fixture#i1/d3')
            after=annotation_context(ledger.eligible('match:fixture','2020-01-01T10:01:00Z'),'match:fixture#i1/d3')
            assert before['confirmed_drops'] is None and before['confirmed_misfields'] is None
            assert after['confirmed_drops'] is None and after['confirmed_misfields']==1
            assert after['disputed_groups']==1
            count=ledger.connection.execute('SELECT COUNT(*) FROM context_records').fetchone()[0]
        finally:ledger.close()
    report={'scope':fixture['scope'],'fixture_license':fixture['license'],'immutable_records':count,'before':before,'after':after,
            'checks':{'duplicate_reorder_idempotent':count==3,'unknown_without_coverage':True,'conflict_retained':True},
            'real_match_incident_annotations':0,'model_features_enabled':False,
            'limitations':'Authored fictional example; no real coach review, video licence or prospective fielding benefit claimed.'}
    (PROJECT_ROOT/'docs/audit/annotations-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
