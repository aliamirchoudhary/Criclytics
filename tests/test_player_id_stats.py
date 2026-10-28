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
from criclytics_app.pipeline.identities import Builder
from criclytics_app.pipeline.player_id_stats import identity_match, export
from criclytics_app.pipeline import cricsheet
from criclytics_app.pipeline.aggregation import aggregate
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.services.json_io import atomic_json
from criclytics_app.services.player_id_stats import PlayerStore

PACK = json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))


class PlayerIdentityStatsTests(unittest.TestCase):
    def candidate(self, root):
        raw = deepcopy(PACK['fixtures'][0]['match'])
        names = sum(raw['info']['players'].values(), [])
        raw['info']['registry'] = {'people': {name: 'id'+str(i) for i, name in enumerate(names)}}
        scored = cricsheet.build_raw_accumulators([])
        builder = Builder()
        batter = raw['innings'][0]['overs'][0]['deliveries'][0]['batter']
        pid = 'player:cricsheet:'+raw['info']['registry']['people'][batter]
        for index in range(3):
            value = deepcopy(raw)
            if index == 1:
                # Rename the complete source representation without changing its identity.
                value = json.loads(json.dumps(value).replace('"'+batter+'"', '"Alias Batter"'))
            if index == 2:
                value['info']['registry']['people'][batter] = 'other'
            builder.add(value, str(index))
            match = identity_match(value, str(index))
            match.update(_file=str(index), _format='Test')
            aggregate([match], scored)
        registry = builder.finish('fixture')
        registry_path = root/'identities.json'; atomic_json(registry_path, registry)
        counts = export(scored, registry, root/'players.sqlite3')
        manifest = {'schema_version': 1, 'dataset_id': 'fixture', 'registry_sha256': digest(registry_path),
                    'database_sha256': digest(root/'players.sqlite3'), **counts}
        atomic_json(root/'manifest.json', manifest)
        return PlayerStore(root, 'fixture', digest(registry_path)), batter, pid, scored

    def test_alias_collision_context_totals_and_read_only_candidate(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            store, name, pid, tables = self.candidate(root)
            profile = store.profile(pid)
            with self.assertRaises(Conflict): store.profile(name)
            self.assertEqual(store.profile('Alias Batter')['identity_id'], pid)
            self.assertIsNone(profile['country'])
            self.assertTrue(profile['observed_teams'])
            self.assertEqual(profile['batting']['Test']['innings'], 4)
            all_scored = {p for p, _ in tables['bat']} | {p for p, _ in tables['bowl']}
            self.assertEqual(sum(p['stats_available'] for p in store.listing({'limit':500})['players']), len(all_scored))
            for fmt, bat in profile['batting'].items():
                for group in ('yearly', 'vs_opp', 'at_venues'):
                    self.assertEqual(sum(row['runs'] for row in profile[group][fmt].values()), bat['runs'])
                self.assertEqual(bat['runs'], tables['bat'][(pid, fmt)]['runs'])
            matches = store.listing({'search': name})
            self.assertEqual(len(matches['players']), 2)
            self.assertEqual(store.listing({'search': 'Alias Batter'})['players'][0]['identity_id'], pid)
            self.assertEqual(store.listing({'search': '%_'})['players'], [])
            self.assertTrue(all(row['identity_id'] for row in store.records()['most_runs']['Test']))
            with store.connect() as db:
                with self.assertRaises(Exception): db.execute('DELETE FROM players')
            with self.assertRaises(ValueError): PlayerStore(root, 'wrong', digest(root/'identities.json'))

    def test_opt_in_api_name_id_search_compare_and_hash(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory); store, name, pid, _ = self.candidate(root)
            # Initialize factory with legacy default, inject this portable fixture registry/store.
            app = create_app({'TESTING': True, 'IDENTITY_REGISTRY': '', 'IDENTITY_PLAYER_STORE': '',
                              'LIVE_DIR': root/'live', 'LIVE_FETCH_ENABLED': False, 'REDIS_URL': ''})
            app.extensions['player_id_store'] = store
            client = app.test_client()
            self.assertEqual(client.get('/api/players/'+name).status_code, 409)
            self.assertEqual(client.get('/api/players/'+pid).json['identity_id'], pid)
            self.assertEqual(client.get('/api/players/Alias%20Batter').json['identity_id'], pid)
            self.assertEqual(client.get('/api/compare/players', query_string={'player_a':pid,'player_b':'Alias Batter'}).json['player_a']['identity_id'], pid)
            self.assertEqual(client.get('/api/players', query_string={'search':name}).json['total'], 2)
            self.assertEqual(client.get('/api/players?sort=unsupported').status_code, 400)
            self.assertTrue(client.get('/api/records').json['identity_correct'])
            self.assertTrue(client.get('/api/rankings?format=Test').json['identity_correct'])
            with (root/'players.sqlite3').open('ab') as stream: stream.write(b'corrupt')
            with self.assertRaises(ValueError): PlayerStore(root, 'fixture', digest(root/'identities.json'))


if __name__ == '__main__': unittest.main()
