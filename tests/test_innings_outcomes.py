from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from criclytics_app.ml.innings_outcomes import extract,fit,predict,score_bin
from test_contextual_scenarios import corpus


class InningsOutcomeTests(unittest.TestCase):
    def test_sequence_target_and_joint_result_have_no_terminal_context(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);corpus(root/'raw')
            raw=json.loads((root/'raw/000.json').read_text())
            players,match=extract(raw,'authored')
            changed=deepcopy(raw)
            for delivery in changed['innings'][0]['overs'][0]['deliveries'][-3:]:
                delivery['runs']={'batter':6,'extras':0,'total':6}
            later,later_match=extract(changed,'authored')
            self.assertEqual(players[0]['keys'],later[0]['keys'])
            self.assertNotEqual(players[0]['target'],later[0]['target'])
            self.assertEqual(match['target'],later_match['target'])
            self.assertEqual([score_bin(n) for n in (0,1,9,10,49,50,99,100)],[0,1,1,2,4,5,6,7])

    def test_heldout_outcomes_do_not_change_fitted_weights_or_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);corpus(root/'raw')
            for path in (root/'raw').glob('*.json'):
                raw=json.loads(path.read_text())
                second=deepcopy(raw['innings'][0]);second['team']='Team X'
                for delivery in second['overs'][0]['deliveries']:
                    delivery.update(batter='X',non_striker='Y',bowler='A')
                raw['innings'].append(second);path.write_text(json.dumps(raw))
            fit(root/'raw',root/'first','2020-12-31')
            for path in sorted((root/'raw').glob('*.json'))[-4:]:
                raw=json.loads(path.read_text());raw['info']['outcome']['winner']='Team X'
                for innings in raw['innings']:
                    for event in innings['overs'][0]['deliveries']:
                        event['runs']={'batter':6,'extras':0,'total':6}
                path.write_text(json.dumps(raw))
            fit(root/'raw',root/'second','2020-12-31')
            for kind in ('player','match'):
                first=json.loads((root/f'first/{kind}-model.json').read_text())
                second=json.loads((root/f'second/{kind}-model.json').read_text())
                for field in ('counts','weights','temperature'):
                    self.assertEqual(first[field],second[field])
                keys=('all','1:0:0','player:cricsheet:aaaaaaaa','player:cricsheet:cccccccc','Authored Ground','Team X') if kind=='player' else ('all','Team A','Team X','Team A|Team X','Authored Ground')
                forms=[[0]*len(first['labels']) for _ in range(1 if kind=='player' else 2)]
                distribution,_=predict(first,keys,forms)
                self.assertAlmostEqual(float(distribution.sum()),1)
                self.assertTrue(np.isfinite(distribution).all())
                if kind=='player':
                    self.assertGreaterEqual(distribution[5:].sum(),distribution[7:].sum())
