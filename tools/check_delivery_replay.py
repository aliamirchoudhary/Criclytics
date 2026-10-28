"""Bounded actual-match replay reconciliation against the corrected innings scorer."""
import json
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.events import EventStore,replay
from criclytics_app.pipeline.scoring import score_match
from criclytics_app.pipeline.schema import normalize_legacy_match
from criclytics_app.pipeline.artifacts import digest


def main():
    path=PROJECT_ROOT/'build/events-t20-v1.sqlite3';store=EventStore(path)
    checked=[]
    try:
        ids=[row[0] for row in store.connection.execute('SELECT match_id FROM matches ORDER BY match_id')]
        for mid in ids:
            metadata=store.metadata(mid)
            raw=PROJECT_ROOT/'data/raw/t20s_male_json'/(metadata['source_id']+'.json')
            assert digest(raw)==metadata['source_file_sha256']
            match=json.loads(raw.read_text(encoding='utf-8'));normalize_legacy_match(match)
            expected=score_match(match)['innings'];actual=replay(metadata,store.events(mid))
            assert len(actual)==len(expected)
            for got,want in zip(actual,expected):
                assert (got['runs'],got['wickets'],got['legal_balls'])==(want['total'],want['wickets'],want['legal_balls']),(mid,got,want)
            checked.append({'match_id':mid,'innings':len(actual),'attempts':sum(r['attempts'] for r in actual)})
        counts={table:store.connection.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('observations','receipts','matches','events')}
        missing_times=store.connection.execute('SELECT COUNT(*) FROM events WHERE available_at IS NULL').fetchone()[0]
        dataset=store.connection.execute("SELECT value FROM build_metadata WHERE key='dataset_id'").fetchone()[0]
    finally:store.close()
    report={'schema_version':1,'dataset_id':dataset,'counts':counts,'store_bytes':path.stat().st_size,
            'unknown_observed_times':missing_times,'matches_reconciled':checked,
            'zero_external_api_calls':True,'limitations':'100 deterministically selected historical maleT20I matches, not whole-corpus or prospective live parity. Corrections/reorder/target revisions tested with portable fictional fixtures. Exact historical event/publication times unknown; derived targets are unverified.'}
    (PROJECT_ROOT/'docs/audit/delivery-replay-2026-10-28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
