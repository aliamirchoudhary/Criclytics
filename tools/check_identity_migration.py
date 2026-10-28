"""Local full-corpus identity migration evidence; no network or automatic provider joins."""
from collections import Counter
import json
from pathlib import Path
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.services.identities import IdentityRegistry
from criclytics_app.services.json_io import read_json


def main():
    registry=PROJECT_ROOT/'build/identities-v1-final.json';data=read_json(registry)
    app=create_app({'PROCESSED_DIR':PROJECT_ROOT/'build/data-v3-manifest-final','IDENTITY_REGISTRY':registry,
                    'LIVE_DIR':PROJECT_ROOT/'build/t017-live','REDIS_URL':'','LIVE_FETCH_ENABLED':False})
    client=app.test_client()
    known=client.get('/api/players/SC%20Cook');assert known.status_code==200
    stable=client.get('/api/players/'+known.json['identity_id']);assert stable.status_code==200
    assert stable.json['batting']==known.json['batting']
    assert client.get('/api/players/A%20Ali').status_code==409
    assert client.get('/api/compare/players?player_a=A%20Ali&player_b=SC%20Cook').status_code==409
    assert client.get('/api/identities/player/player:cricsheet:13bee186').status_code==200
    historical_dates={date for row in data['entities']['match'].values() for date in row['dates']}
    raw=read_json(PROJECT_ROOT/'data/live/matches.json');rows=raw.get('data',raw)
    if isinstance(rows,dict):rows=rows.get('data') or rows.get('matches') or []
    overlaps=[{'provider_id':row.get('id'),'date':row.get('date'),'status':'requires_review_no_automatic_join'} for row in rows if row.get('date') in historical_dates]
    labels={name for row in data['entities']['player'].values() for name in row['source_names']}
    source_collisions=[name for name in labels if len(data['aliases']['player'].get(name.casefold(),[]))>1]
    result={'dataset_id':data['dataset_id'],'registry_sha256':digest(registry),'registry_bytes':registry.stat().st_size,
            'counts':{kind:len(values) for kind,values in data['entities'].items()},'source_player_labels':len(labels),
            'colliding_source_player_labels':len(source_collisions),'unresolved_reasons':dict(Counter(row['reason'] for row in data['unresolved'])),
            'register_sha256':data['register_sha256'],'observed_multi_team_players':sum(len(row['memberships'])>1 for row in data['entities']['player'].values()),
            'canonical_venues':sum(':cricsheet:' in key for key in data['entities']['venue']),
            'provisional_venues':sum(':local:' in key for key in data['entities']['venue']),
            'provider_cached_rows_reviewed':len(rows),'possible_date_overlaps':overlaps,
            'real_verified_provider_match_links':len(data['reviewed_match_links']),
            'checks':{'name_stable_profile_parity':True,'ambiguous_profile_409':True,'ambiguous_comparison_409':True,'identity_metadata':True},
            'limitations':'Provider cache review is offline and not evidence of live completeness. No real match join is invented; cross-provider confirmed duplicates are covered by portable fictional fixtures. Legacy name aggregates remain under review; default dataset/identity configuration unchanged.'}
    (PROJECT_ROOT/'docs/audit/identity-migration-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
