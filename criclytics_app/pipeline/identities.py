"""Build stable, source-attributed cricket identities without fuzzy merges."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from .artifacts import validate,digest
from ..services.json_io import atomic_json,read_json


def key(value): return str(value).strip().casefold()


def local_id(kind,*values):
    return kind+':local:'+hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()[:24]


class Builder:
    def __init__(self,register=None):
        self.entities={k:{} for k in ('player','team','venue','match')}
        self.aliases={k:defaultdict(set) for k in self.entities}
        self.provider_maps={k:{} for k in self.entities}
        self.unresolved=[]
        self.register={k:{} for k in ('player','venue')}
        self.register_alias={k:defaultdict(set) for k in self.register}
        self.register_hashes={}
        if register:
            for kind,base,aliases in [('player','people.csv','names.csv'),('venue','venues.csv','venue_names.csv')]:
                for filename in (base,aliases):self.register_hashes[filename]=digest(Path(register)/filename)
                with (Path(register)/base).open(encoding='utf-8-sig',newline='') as stream:
                    for row in csv.DictReader(stream):
                        identifier=kind+':cricsheet:'+row['identifier']
                        self.register[kind][identifier]=row
                        for name in (row.get('name'),row.get('unique_name')):
                            if name:self.register_alias[kind][key(name)].add(identifier)
                with (Path(register)/aliases).open(encoding='utf-8-sig',newline='') as stream:
                    for row in csv.DictReader(stream):self.register_alias[kind][key(row['name'])].add(kind+':cricsheet:'+row['identifier'])

    def entity(self,kind,identifier,name,source_name=True):
        item=self.entities[kind].setdefault(identifier,{'id':identifier,'name':name,'aliases':set(),'source_names':set(),'source_ids':{},'memberships':{}})
        item['aliases'].add(name)
        if source_name:item['source_names'].add(name)
        self.aliases[kind][key(name)].add(identifier)
        return item

    def add(self,match,source_id):
        info=match['info'];gender=info['gender'];team_type=info['team_type']
        if 'match:cricsheet:'+str(source_id) in self.entities['match']:raise ValueError('Duplicate source match identifier; explicit reconciliation required')
        dates=sorted(str(d) for d in info['dates']);people=info.get('registry',{}).get('people',{})
        team_ids={}
        for name in info['teams']:
            identifier=local_id('team',gender,team_type,name)
            self.entity('team',identifier,name)['scope']={'gender':gender,'team_type':team_type}
            team_ids[name]=identifier
        venue_name=info.get('venue','Unknown venue')
        candidates=self.register_alias['venue'].get(key(venue_name),set())
        vid=next(iter(candidates)) if len(candidates)==1 else local_id('venue',venue_name,info.get('city'))
        venue=self.entity('venue',vid,venue_name)
        if len(candidates)>1:self.unresolved.append({'kind':'venue','name':venue_name,'candidates':sorted(candidates),'reason':'ambiguous_register_alias'})
        for team,names in info['players'].items():
            for name in names:
                pid='player:cricsheet:'+people[name] if name in people else local_id('player',source_id,name)
                player=self.entity('player',pid,name)
                if name in people:player['source_ids']['cricsheet']=people[name]
                if name not in people:self.unresolved.append({'kind':'player','name':name,'match':source_id,'reason':'missing_source_identity'})
                membership=player['memberships'].setdefault(team_ids[team],{'team_id':team_ids[team],'team_name':team,'first_date':dates[0],'last_date':dates[-1],'matches':0})
                membership['first_date']=min(membership['first_date'],dates[0]);membership['last_date']=max(membership['last_date'],dates[-1]);membership['matches']+=1
        mid='match:cricsheet:'+str(source_id)
        item=self.entity('match',mid,str(source_id));item.update({'teams':[team_ids[t] for t in info['teams']],'dates':dates,'venue_id':vid,'format':info['match_type'],'gender':gender})
        item['source_ids']['cricsheet']=str(source_id)
        self.provider_maps['match']['cricsheet:'+str(source_id)]=mid

    def finish(self,dataset_id):
        for kind in ('player','venue'):
            aliases_by_id=defaultdict(list)
            for alias,ids in self.register_alias[kind].items():
                for identifier in ids:aliases_by_id[identifier].append(alias)
            for identifier,item in self.entities[kind].items():
                row=self.register[kind].get(identifier)
                if not row:continue
                for alias in aliases_by_id[identifier]:self.aliases[kind][alias].add(identifier)
                for field,value in row.items():
                    if field.startswith('key_') and value:
                        provider=field[4:];token=provider+':'+value
                        old=self.provider_maps[kind].get(token)
                        if old and old!=identifier:
                            self.unresolved.append({'kind':kind,'source':provider,'source_id':value,'candidates':[old,identifier],'reason':'provider_identifier_collision'})
                            self.provider_maps[kind][token]=None
                        elif token not in self.provider_maps[kind]:self.provider_maps[kind][token]=identifier
                        item['source_ids'][provider]=value
                item['source_ids']['cricsheet']=identifier.split(':')[-1]
        for kind,entities in self.entities.items():
            for item in entities.values():
                item['aliases']=sorted(item['aliases']);item['source_names']=sorted(item['source_names']);item['memberships']=sorted(item['memberships'].values(),key=lambda m:m['team_id'])
        aliases={kind:{name:sorted(ids) for name,ids in sorted(values.items())} for kind,values in self.aliases.items()}
        collisions=[{'kind':kind,'alias':name,'candidates':ids,'reason':'name_collision'} for kind,values in aliases.items() for name,ids in values.items() if len(ids)>1]
        return {'schema_version':1,'dataset_id':dataset_id,'attribution':'Cricsheet JSON and People/Venue Registers (ODC-BY-1.0); derived identity mappings by Criclytics.',
                'register_sha256':self.register_hashes,'entities':self.entities,'aliases':aliases,'provider_maps':self.provider_maps,
                'unresolved':self.unresolved+collisions,'reviewed_match_links':[]}


def build(raw,dataset,register=None):
    manifest=validate(dataset);builder=Builder(register)
    rejected={row['path'] for row in read_json(Path(dataset)/'difference_report.json')['rejected']}
    for row in manifest['inputs']:
        if row['path'] in rejected:continue
        path=(Path(raw)/row['path']).resolve()
        if not path.is_relative_to(Path(raw).resolve()) or digest(path)!=row['sha256']:raise ValueError('Source hash/path mismatch')
        builder.add(read_json(path),path.stem)
    return builder.finish(manifest['dataset_id'])


def reviewed_link(registry,provider,source_id,target,evidence,reviewer):
    if target not in registry['entities']['match'] or not evidence or not reviewer:raise ValueError('Reviewed link requires target, evidence and reviewer')
    token=provider+':'+str(source_id)
    old=registry['provider_maps']['match'].get(token)
    if old and old!=target:raise ValueError('Conflicting reviewed match link')
    registry['provider_maps']['match'][token]=target
    registry['reviewed_match_links'].append({'provider':provider,'source_id':str(source_id),'target':target,'evidence':evidence,'reviewer':reviewer})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir',type=Path,required=True);parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--register-dir',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Use a fresh registry output; preserve previous versions')
    atomic_json(args.output,build(args.raw_dir,args.dataset,args.register_dir))


if __name__=='__main__':main()
