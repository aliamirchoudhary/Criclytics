"""Offline bounded source-ID matchup/phase evidence, never a prediction."""
import argparse
from collections import defaultdict
from pathlib import Path
from .events import EventStore, checksum
from .artifacts import digest
from .scoring import NOT_DISMISSED, BOWLER_WICKETS
from ..services.json_io import atomic_json
from ..paths import PACKAGE_ROOT, PROJECT_ROOT


def build(source, output):
    output=Path(output).resolve()
    if output.exists() or any(output==p or output.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist',PROJECT_ROOT/'data')):
        raise ValueError('Use a fresh private evidence output')
    pairs,phases=defaultdict(lambda:defaultdict(int)),defaultdict(lambda:defaultdict(int))
    store=EventStore(source,readonly=True);total=0;dates=[];payloads=[]
    try:
        store.connection.execute('BEGIN')
        dataset=store.connection.execute("SELECT value FROM build_metadata WHERE key='dataset_id'").fetchone()[0]
        matches=store.connection.execute('SELECT match_id FROM matches ORDER BY match_id LIMIT 101').fetchall()
        if not 1<=len(matches)<=100:raise ValueError('Use an explicit1..100match historical archive')
        for mid, in matches:
            meta=store.metadata(mid);dates.extend(meta['dates'])
            for event in store.events(mid):
                payloads.append(checksum(event))
                if event['kind']!='delivery' or meta['innings'][event['innings']-1]['super_over']:continue
                total+=1
                if total>50000:raise ValueError('Delivery evidence budget exceeded')
                fmt=meta['format'];batter=event['striker'];bowler=event['bowler']
                phase='powerplay' if event['over']<6 else 'middle' if event['over']<15 else 'death'
                if fmt!='T20I':phase='unclassified'
                for row in (pairs[batter+'|'+bowler+'|'+fmt], phases[batter+'|'+fmt+'|'+phase]):
                    row['attempts']+=1;row['batter_runs']+=event['runs']['batter']
                    row['batter_balls']+=int(not event['extras'].get('wides'))
                    row['striker_dismissals']+=sum(w['player_id']==batter and w['kind'] not in NOT_DISMISSED for w in event['wickets'])
                    row['bowler_credited_wickets']+=sum(w['player_id']==batter and w['kind'] in BOWLER_WICKETS for w in event['wickets'])
    finally:store.close()
    result={'schema_version':1,'dataset_id':dataset,'source_event_hash':checksum(payloads),'source_store_sha256':digest(source),
            'matches':len(matches),'attempts':total,'first_match_date':min(dates),'last_match_date':max(dates),
            'historical_publication_availability':None,'pairs':dict(pairs),'phases':dict(phases),
            'scope':'Explicit historical archive subset; not complete head-to-head careers. Pair/phase rows are not conditioned on selected opponent or venue.',
            'attribution':'Cricsheet JSON, ODC-BY-1.0; derived historical delivery evidence.'}
    atomic_json(output,result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=build(args.source,args.output);print({k:v for k,v in result.items() if k not in ('pairs','phases')})
