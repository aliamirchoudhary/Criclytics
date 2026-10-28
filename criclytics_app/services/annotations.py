"""Attributed observations, not assumed complete coverage or latent pressure labels."""
from collections import defaultdict
import re
from .weather import utc

TYPES={'dropped_catch','misfield','missed_chance','on_field_incident'}


def position(event_id):
    match=re.fullmatch(r'(.+)#i([1-9][0-9]*)/d([1-9][0-9]*)',str(event_id))
    if not match:raise ValueError('Annotation requires canonical delivery-attempt identity')
    return match[1],int(match[2]),int(match[3])


def validate_annotation(record):
    value=record['value'];mid,_,_=position(value.get('event_id'))
    if mid!=record['match_id'] or value.get('annotation_kind') not in TYPES:raise ValueError('Invalid annotation target/type')
    if record['kind']=='fielding' and value['annotation_kind']=='on_field_incident':raise ValueError('Incident is not a fielding label')
    if value.get('occurred') is not None and type(value['occurred']) is not bool:raise ValueError('Occurred must be true/false/unknown')
    if value.get('confidence') not in ('observed','uncertain','disputed'):raise ValueError('Observation confidence required')
    if value.get('review_state') not in ('submitted','reviewed','rejected'):raise ValueError('Review state required')
    if value['review_state']=='reviewed' and not value.get('reviewer'):raise ValueError('Reviewed annotation requires reviewer attribution')
    if value.get('event_time') and utc(value['event_time'])>utc(record['observed_at']):raise ValueError('Annotation observed before event')
    allowed={'event_id','annotation_kind','occurred','confidence','review_state','reviewer','event_time','player_id','chance_id'}
    if set(value)-allowed:raise ValueError('Free text/tactical notes require separate private workflow')
    if value.get('player_id') and not str(value['player_id']).startswith('player:'):raise ValueError('Actor must be stable identity or unknown')
    return record


def annotation_context(records,before_event_id):
    target_mid,target_innings,target_attempt=position(before_event_id)
    groups=defaultdict(list)
    for record in records:
        if record['kind'] not in ('fielding','incident'):continue
        value=record['value'];mid,innings,attempt=position(value['event_id'])
        if mid!=target_mid or (innings,attempt)>=(target_innings,target_attempt):continue
        if value['review_state']=='rejected':continue
        groups[(value['event_id'],value['annotation_kind'],value.get('chance_id') or 'unspecified')].append(record)
    resolved=[]
    for (event_id,kind,chance_id),items in sorted(groups.items(),key=lambda pair:str(pair[0])):
        reviewed=[record for record in items if record['value']['review_state']=='reviewed']
        candidates=reviewed or items
        observations={r['value'].get('occurred') for r in candidates if r['value']['confidence']=='observed'}
        uncertain=any(r['value']['confidence']!='observed' for r in candidates)
        conflict=len(observations)>1 or uncertain
        known=next(iter(observations)) if len(observations)==1 and not conflict else None
        actors={r['value'].get('player_id') for r in candidates if r['value'].get('player_id')}
        player_id=next(iter(actors)) if len(actors)==1 else None
        resolved.append({'event_id':event_id,'annotation_kind':kind,'chance_id':chance_id,'player_id':player_id,'actor_conflict':len(actors)>1,'occurred':known,
                         'status':'conflict_or_uncertain' if conflict else 'reviewed' if reviewed else 'unreviewed',
                         'record_revisions':[{'id':r['record_id'],'revision':r['revision'],'source':r['source'],'observer':r['observer']} for r in sorted(candidates,key=lambda r:r['record_id'])]})
    result={'available':bool(resolved),'coverage':'partial attributed observations only','observations':resolved,
            'confirmed_drops':None,'confirmed_misfields':None,'disputed_groups':sum(r['status']=='conflict_or_uncertain' for r in resolved)}
    for kind,key in [('dropped_catch','confirmed_drops'),('misfield','confirmed_misfields')]:
        known=[r for r in resolved if r['annotation_kind']==kind and r['occurred'] is not None and r['status']=='reviewed']
        if known:result[key]=sum(r['occurred'] is True for r in known)
    return result
