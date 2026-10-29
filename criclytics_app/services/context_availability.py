"""As-issued context coverage, not fitted features or inferred mental states."""
import json
import math

from .annotations import annotation_context
from .weather import FIELDS, utc

FAMILIES = ('weather','home_away','pitch','fielding','captaincy','crowd')


def validate_extension(record):
    value, kind = record['value'],record['kind']
    if record.get('rights_basis') not in ('own_observation','permitted_extract','licensed'):
        raise ValueError('Observation reuse basis required')
    if not record.get('rights_reference') or len(str(record['rights_reference']))>500:
        raise ValueError('Observation rights reference required')
    if kind=='weather_observation':
        if set(value)-{'venue_id','valid_until',*FIELDS} or not value.get('venue_id'):
            raise ValueError('Bounded weather fields/venue required')
        if utc(value['valid_until'])<=utc(record['effective_at']):
            raise ValueError('Weather validity must follow observation')
        if not any(value.get(field) is not None for field in FIELDS):
            raise ValueError('At least one observed weather measurement required')
        for field,(low,high) in FIELDS.items():
            number = value.get(field)
            if number is not None and (type(number) not in (int,float) or not math.isfinite(number) or not low<=number<=high):
                raise ValueError('Invalid observed weather measurement')
    elif kind=='captaincy':
        if (set(value)-{'team_id','captain_id','change_confirmed'} or not value.get('team_id')
                or not str(value.get('captain_id','')).startswith('player:')
                or type(value.get('change_confirmed')) is not bool):
            raise ValueError('Sourced captain/team/change required; pressure is not an input')
    else:
        if (set(value)-{'venue_id','event_kind','occurred','event_id'} or not value.get('venue_id')
                or value.get('event_kind') not in ('booing','support','on_field_disruption')
                or value.get('occurred') is not None and type(value['occurred']) is not bool):
            raise ValueError('Attributed crowd observation required; no emotional score')
        from .annotations import position
        if position(value.get('event_id'))[0]!=record['match_id']:
            raise ValueError('Crowd event must identify the same match attempt')


def summarize(records,cutoff,venue_id='',team_id='',before_event_id=None):
    """Input must already be scope/revision/availability filtered by ContextLedger."""
    when = utc(cutoff)
    groups = {name:[] for name in FAMILIES}
    kind_family = {'weather_observation':'weather','venue_affiliation':'home_away','pitch_report':'pitch',
                   'fielding':'fielding','incident':'fielding','captaincy':'captaincy','crowd_event':'crowd'}
    for record in records:
        if max(utc(record[k]) for k in ('published_at','observed_at','effective_at'))>when:
            continue
        value, kind = record['value'],record['kind']
        family = kind_family.get(kind)
        if not family or value.get('venue_id') and value['venue_id']!=venue_id or value.get('team_id') and value['team_id']!=team_id:
            continue
        if kind=='weather_observation' and utc(value['valid_until'])<=when:
            continue
        if kind in ('fielding','incident','crowd_event'):
            if not before_event_id:
                continue
            from .annotations import position
            if position(value['event_id'])[1:]>=position(before_event_id)[1:]:
                continue
        groups[family].append(record)
    output = {}
    for family,rows in groups.items():
        signatures = {json.dumps(r['value'],sort_keys=True) for r in rows}
        conflict = len(signatures)>1 if family not in ('fielding','crowd') else False
        status = 'unknown' if not rows else 'conflict' if conflict else 'observed_not_modelled'
        result = {'status':status,'model_enabled':False,'value':rows[0]['value'] if len(signatures)==1 else None,
                  'records':[{'record_id':r['record_id'],'revision':r['revision'],'source':r['source'],
                    'observer':r['observer'],'published_at':r['published_at'],'observed_at':r['observed_at'],
                    'effective_at':r['effective_at']} for r in rows]}
        if family=='fielding' and before_event_id:
            result['observations'] = annotation_context(rows,before_event_id)
            if result['observations']['disputed_groups']:
                result['status']='conflict'
        if family=='crowd':
            result['value']=None  # distinct events are not a global crowd/pressure score
            result['events']=[r['value'] for r in rows]
        output[family]=result
    return {'schema_version':1,'as_of':cutoff,'families':output,'model_effect':'none',
            'coverage':'Partial attributed observations only; unknown is not false.',
            'limitations':['No psychological/politics state inferred.','Rain does not imply a fixed bounce penalty.',
                           'Feature inclusion requires a preregistered as-issued ablation.']}
