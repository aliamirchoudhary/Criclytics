"""Identity-correct preparation evidence, explicit missing context and no private input."""
from pathlib import Path
from werkzeug.exceptions import NotFound, ServiceUnavailable
from .json_io import read_json
from ..pipeline.events import checksum
from ..pipeline.artifacts import digest
from ..paths import PACKAGE_ROOT, PROJECT_ROOT


def initialize(app):
    app.extensions['scouting_sample']=None
    path=app.config['SCOUTING_SAMPLE']
    if not path:return
    path=Path(path).resolve()
    if any(path.is_relative_to(p) for p in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')) or path.stat().st_size>4*1024*1024:
        raise ValueError('Scouting evidence must be bounded/private')
    sample=read_json(path);store=app.extensions['player_id_store']
    if not store or sample.get('schema_version')!=1 or sample.get('dataset_id')!=store.manifest['dataset_id']:
        raise ValueError('Scouting evidence must match identity dataset')
    app.extensions['scouting_sample']={'sha256':digest(path),'data':sample}


def report(app, player, bowler=None, fmt='T20I', opponent='', venue=''):
    store=app.extensions['player_id_store']
    if not store:raise ServiceUnavailable('Identity-correct player evidence is not configured')
    p=store.profile(player)
    if not p:raise NotFound('Player not found')
    b=store.profile(bowler) if bowler else None
    if bowler and not b:raise NotFound('Bowler not found')
    sample=app.extensions['scouting_sample'];data=sample['data'] if sample else {}
    phases={phase:data.get('phases',{}).get(p['identity_id']+'|'+fmt+'|'+phase) for phase in ('powerplay','middle','death')}
    matchup=data.get('pairs',{}).get(p['identity_id']+'|'+b['identity_id']+'|'+fmt) if b else None
    result={'schema_version':1,'dataset_id':store.manifest['dataset_id'],'player_store_sha256':store.manifest['database_sha256'],
            'player':{'identity_id':p['identity_id'],'name':p['name'],'observed_teams':p['observed_teams']},
            'format':fmt,'selected_opponent':opponent or None,'selected_venue':venue or None,
            'options':{'opponents':sorted(p['vs_opp'].get(fmt,{})), 'venues':sorted(p['at_venues'].get(fmt,{}))},
            'batting':p['batting'].get(fmt),'bowling':b['bowling'].get(fmt) if b else None,
            'bowler':{'identity_id':b['identity_id'],'name':b['name']} if b else None,
            'yearly':p['yearly'].get(fmt,{}),'against_opponent':p['vs_opp'].get(fmt,{}).get(opponent),
            'at_venue':p['at_venues'].get(fmt,{}).get(venue),'recent_innings_all_formats':p['recent_form'],
            'matchup':matchup,'phases':phases,'delivery_sample':{k:v for k,v in data.items() if k not in ('pairs','phases')} if sample else None,
            'delivery_sample_sha256':sample['sha256'] if sample else None,
            'coverage':read_json(Path(app.config['PROCESSED_DIR'])/'coverage.json'),
            'assumptions':'Descriptive slices only. Venue/opponent selection is not a causal advantage or a forecast. Pair/phase evidence uses its separate declared archive.',
            'missing_context':['weather','pitch tracking','field placements','mental state','unreviewed incidents'],
            'attribution':'Cricsheet JSON and registers (ODC-BY-1.0); derived Criclytics source-ID summaries.'}
    return {'report_id':checksum(result),**result}
