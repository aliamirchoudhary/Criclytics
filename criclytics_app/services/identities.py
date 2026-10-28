"""Immutable, dataset-bound identity lookups; ambiguous names never pick a first result."""
from copy import deepcopy
from werkzeug.exceptions import Conflict
from .json_io import read_json


class IdentityRegistry:
    def __init__(self,data=None):self.data=data

    def resolve(self,kind,value):
        if not self.data:return None
        entities=self.data['entities'][kind]
        if value in entities:return deepcopy(entities[value])
        ids=self.data['aliases'][kind].get(str(value).strip().casefold(),[])
        if len(ids)>1:raise Conflict('Ambiguous name; use a stable identity identifier')
        return deepcopy(entities[ids[0]]) if ids else None

    def source_name(self,kind,value):
        record=self.resolve(kind,value)
        if not record:return value,None
        names=record['source_names']
        exact=[name for name in names if name.casefold()==str(value).strip().casefold()]
        if len(exact)==1:names=exact
        if len(names)!=1:raise Conflict('Identity has multiple historical labels; aggregate statistics require identity-aware regeneration')
        # A source label itself must not combine two distinct people/venues.
        if len(self.data['aliases'][kind].get(names[0].casefold(),[]))!=1:raise Conflict('Source label is ambiguous; aggregate unavailable')
        return names[0],record['id']

    def match(self,source_id,provider='cricsheet'):
        return self.data['provider_maps']['match'].get(provider+':'+str(source_id)) if self.data else None


def initialize(app):
    from pathlib import Path
    path=app.config['IDENTITY_REGISTRY']
    data=None
    if path:
        data=read_json(path)
        manifest=read_json(Path(app.config['PROCESSED_DIR'])/'manifest.json')
        if data.get('schema_version')!=1 or not data.get('dataset_id') or data['dataset_id']!=manifest.get('dataset_id'):raise ValueError('Identity registry must match selected dataset')
        for kind in ('player','team','venue','match'):
            if not isinstance(data['entities'][kind],dict) or not isinstance(data['aliases'][kind],dict):raise ValueError('Invalid identity registry')
    app.extensions['identity_registry']=IdentityRegistry(data)
