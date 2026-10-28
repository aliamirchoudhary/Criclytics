"""Optional as-issued weather context; no network or inferred pitch/psychology values."""
from collections import deque
from datetime import datetime,timezone
import math
from zoneinfo import ZoneInfo

FIELDS={'temperature_c':(-90,65),'relative_humidity_pct':(0,100),'wind_ms':(0,150),'rain_mm_hour':(0,500)}


def utc(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('Timezone-aware timestamp required')
    return result.astimezone(timezone.utc)


def local_to_utc(value,zone,fold=None):
    local=datetime.fromisoformat(value)
    if local.tzinfo is not None:raise ValueError('Local input must have no offset; zone is explicit')
    timezone_info=ZoneInfo(zone)
    choices=[local.replace(tzinfo=timezone_info,fold=i) for i in (0,1)]
    valid=[candidate for candidate in choices if candidate.astimezone(timezone.utc).astimezone(timezone_info).replace(tzinfo=None)==local]
    if not valid:raise ValueError('Nonexistent local time')
    if choices[0].utcoffset()!=choices[1].utcoffset() and fold is None:raise ValueError('Ambiguous local time requires explicit fold')
    if fold not in (None,0,1):raise ValueError('Invalid fold')
    selected=choices[fold or 0]
    if selected not in valid:raise ValueError('Invalid local time fold')
    return selected.astimezone(timezone.utc).isoformat()


def validate_location(location):
    if not location.get('venue_id') or not location.get('source'):raise ValueError('Location provenance required')
    if not -90<=location['latitude']<=90 or not -180<=location['longitude']<=180:raise ValueError('Invalid coordinates')
    ZoneInfo(location['timezone']);utc(location['known_at'])
    return location


def validate_record(record):
    if record.get('schema_version')!=1 or record.get('kind') not in ('forecast','reanalysis','manual_observation'):raise ValueError('Invalid weather contract')
    if not record.get('source') or not record.get('license') or not record.get('venue_id'):raise ValueError('Weather provenance required')
    if utc(record['valid_until'])<=utc(record['valid_from']):raise ValueError('Invalid weather validity')
    utc(record['observed_at'])
    if record.get('issued_at') and utc(record['issued_at'])>utc(record['observed_at']):raise ValueError('Forecast cannot be observed before issue')
    if type(record.get('resolution_minutes')) is not int or record['resolution_minutes']<1:raise ValueError('Weather resolution required')
    for name,(low,high) in FIELDS.items():
        value=record.get('values',{}).get(name)
        if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high):raise ValueError('Invalid weather value')
    return record


class WeatherCache:
    def __init__(self,maximum=128):
        if not 1<=maximum<=128:raise ValueError('Weather cache bound must be1..128')
        self.records=deque(maxlen=maximum)

    def add(self,record):
        from copy import deepcopy
        self.records.append(deepcopy(validate_record(record)))

    def select(self,location,cutoff):
        missing={'available':False,'values':{name:None for name in FIELDS},'reason':'No eligible as-of weather context','provenance':None}
        if location is None or cutoff is None:return missing
        validate_location(location);when=utc(cutoff)
        if utc(location['known_at'])>when:return missing
        eligible=[]
        for record in self.records:
            if record['venue_id']!=location['venue_id'] or record['kind']=='reanalysis' or not record.get('issued_at'):continue
            if utc(record['issued_at'])<=when and utc(record['observed_at'])<=when and utc(record['valid_from'])<=when<utc(record['valid_until']):eligible.append(record)
        if not eligible:return missing
        record=max(eligible,key=lambda row:(utc(row['issued_at']),utc(row['observed_at'])))
        return {'available':True,'values':{name:record.get('values',{}).get(name) for name in FIELDS},'reason':None,
                'provenance':{name:record.get(name) for name in ('source','license','issued_at','valid_from','valid_until','observed_at','resolution_minutes','kind')}}
