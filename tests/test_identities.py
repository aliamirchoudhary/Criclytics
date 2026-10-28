from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from werkzeug.exceptions import Conflict
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.identities import Builder,reviewed_link,build
from criclytics_app.pipeline.rebuild import rebuild
from criclytics_app.services.identities import IdentityRegistry
from criclytics_app.services.match_listing import listing
from criclytics_app.services.json_io import atomic_json

PACK=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


class IdentityTests(unittest.TestCase):
    def test_same_name_transfer_alias_and_reviewed_match_link(self):
        value=deepcopy(PACK['fixtures'][0]['match']); info=value['info']
        info['registry']={'people':{name:'pid'+str(i) for i,name in enumerate(sum(info['players'].values(),[]))}}
        builder=Builder()
        builder.add(value,'one')
        renamed=deepcopy(value);old=info['players'][info['teams'][0]][0]
        renamed['info']['players'][info['teams'][0]][0]='Renamed Person'
        renamed['info']['registry']['people']['Renamed Person']=info['registry']['people'][old]
        builder.add(renamed,'two')
        transferred=deepcopy(value)
        first,second=info['teams']
        transferred['info']['players'][first].remove(old);transferred['info']['players'][second].append(old)
        builder.add(transferred,'three')
        collision=deepcopy(value);collision['info']['registry']['people'][old]='different-person';builder.add(collision,'four')
        data=builder.finish('fixture-dataset');registry=IdentityRegistry(data)
        with self.assertRaises(Conflict):registry.resolve('player',old)
        person=registry.resolve('player','player:cricsheet:'+info['registry']['people'][old])
        self.assertIn('Renamed Person',person['aliases']);self.assertEqual(len(person['memberships']),2)
        with self.assertRaises(Conflict):registry.source_name('player',person['id'])
        reviewed_link(data,'cricapi','provider-uuid','match:cricsheet:one','Fictional fixture identity verified','fixture-test')
        result=listing([{'id':'provider-uuid','teams':info['teams']}],[{'id':'one','teams':info['teams']}],{},registry)
        self.assertEqual(result['pagination']['total'],1)
        self.assertEqual(result['data'][0]['id'],'one')
        self.assertEqual(len(result['data'][0]['source_refs']),2)
        self.assertEqual(len(data['reviewed_match_links']),1)
        with self.assertRaises(ValueError):reviewed_link(data,'cricapi','provider-uuid','match:cricsheet:two','conflict','fixture-test')
        # An unreviewed lookalike remains a separate match.
        self.assertEqual(listing([{'id':'unreviewed','teams':info['teams']}],[{'id':'one','teams':info['teams']}],{},registry)['pagination']['total'],2)

    def test_register_venue_aliases_and_name_url_compatibility(self):
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);register=root/'register';register.mkdir()
            for filename,text in {'people.csv':'identifier,name,unique_name\npid,Player,Player\n','names.csv':'identifier,name\npid,Player Alias\n','venues.csv':'identifier,name,unique_name\nv1,Fictional Ground,Fictional Ground\n','venue_names.csv':'identifier,name\nv1,Renamed Ground\n'}.items():(register/filename).write_text(text)
            value=deepcopy(PACK['fixtures'][0]['match'])
            builder=Builder(register);builder.add(value,'first')
            value['info']['venue']='Renamed Ground';builder.add(value,'second')
            reg=IdentityRegistry(builder.finish('test'))
            self.assertEqual(reg.resolve('venue','Fictional Ground')['id'],reg.resolve('venue','Renamed Ground')['id'])
            raw=root/'raw/tests_male_json';raw.mkdir(parents=True)
            value=deepcopy(PACK['fixtures'][0]['match']);names=sum(value['info']['players'].values(),[])
            value['info']['registry']={'people':{name:'id'+str(i) for i,name in enumerate(names)}}
            (raw/'fixture.json').write_text(json.dumps(value))
            dataset=root/'dataset';rebuild(root/'raw',dataset)
            identities=build(root/'raw',dataset)
            path=root/'identities.json';atomic_json(path,identities)
            app=create_app({'PROCESSED_DIR':dataset,'IDENTITY_REGISTRY':path,'LIVE_DIR':root/'live','REDIS_URL':'','LIVE_FETCH_ENABLED':False})
            client=app.test_client();pid='player:cricsheet:id0'
            self.assertEqual(client.get('/api/players/'+names[0]).json['identity_id'],pid)
            self.assertEqual(client.get('/api/players/'+pid).json['name'],names[0])
            self.assertEqual(client.get('/api/identities/player/'+pid).json['identity']['source_ids']['cricsheet'],'id0')
            identities['dataset_id']='wrong';atomic_json(path,identities)
            with self.assertRaises(ValueError):create_app({'PROCESSED_DIR':dataset,'IDENTITY_REGISTRY':path})
