import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from criclytics_app import create_app
from criclytics_app.pipeline.rebuild import rebuild
from criclytics_app.pipeline.artifacts import validate,promote,selected,digest
from criclytics_app.paths import PROJECT_ROOT


class ArtifactTests(unittest.TestCase):
    def test_subset_inventory_restore_and_corruption(self):
        pack=json.loads((PROJECT_ROOT/'tests/fixtures/cricket_golden.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory,contextlib.redirect_stdout(io.StringIO()):
            root=Path(directory);raw=root/'raw'
            folders={'Test':'tests_male_json','ODI':'odis_male_json','T20':'t20s_male_json'}
            for fixture in pack['fixtures']:
                path=raw/folders[fixture['match']['info']['match_type']]/(fixture['id']+'.json')
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(fixture['match']))
            other=raw/'unknown/ignored.json';other.parent.mkdir();other.write_text('{}')
            first,second=root/'first',root/'second'
            rebuild(raw,first,limit=3);rebuild(raw,second)
            manifest=validate(first)
            self.assertEqual(manifest['inventory_files'],6)
            self.assertEqual(len(manifest['inputs']),3)
            self.assertEqual(len(manifest['excluded']),3)
            store=root/'store'
            one=promote(first,store,digest(first/'manifest.json'))
            two=promote(second,store)
            self.assertEqual(selected(store),two)
            self.assertEqual(json.loads((store/'current.json').read_text())['previous_id'],one.name)
            promote(one,store)
            self.assertEqual(selected(store),one)
            self.assertTrue(two.is_dir())
            app=create_app({'DATASET_STORE':store,'LIVE_DIR':root/'live','REDIS_URL':'','LIVE_FETCH_ENABLED':False})
            coverage=app.test_client().get('/api/coverage').json
            self.assertTrue(coverage['available'])
            self.assertEqual(coverage['dataset_id'],one.name)
            self.assertEqual(coverage['accepted_matches'],3)
            (second/'players_index.json').write_text('{}')
            with self.assertRaises(ValueError):promote(second,store)
            self.assertEqual(selected(store),one)
            (first/'records.json').unlink()
            with self.assertRaises((ValueError,OSError)):validate(first)
            pointer=store/'current.json';old=pointer.read_bytes();pointer.write_text('{"dataset_id":"../../private"}')
            with self.assertRaises(ValueError):selected(store)
            pointer.write_bytes(old)
