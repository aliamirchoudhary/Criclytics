from copy import deepcopy
import unittest
from tools.media_research import eligible,agreement


class MediaResearchTests(unittest.TestCase):
    def test_no_psychological_ground_truth_or_late_proxy(self):
        row={'proxy':'critical_headline_tone','match_id':'match:a','player_id':'player:a','source':'authored fixture',
             'source_license':'CC0','source_rights_verified':True,'language':'en','published_at':'2020-01-01T10:00:00Z','observed_at':'2020-01-01T10:01:00Z','occurred':None}
        self.assertFalse(eligible(row,'2020-01-01T10:00:30Z'));self.assertTrue(eligible(row,'2020-01-01T11:00:00Z'))
        self.assertFalse(eligible(row,'2020-01-05T11:00:00Z'))
        bad=deepcopy(row);bad['pressure_ground_truth']=True
        with self.assertRaises(ValueError):eligible(bad,'2020-01-01T11:00:00Z')
        row['source_rights_verified']=False;self.assertFalse(eligible(row,'2020-01-01T11:00:00Z'))

    def test_agreement_missing_and_constant_are_not_fake_certainty(self):
        self.assertIsNone(agreement([None],[True])['agreement'])
        self.assertIsNone(agreement([True,True],[True,True])['kappa'])
        self.assertAlmostEqual(agreement([True,False],[True,False])['kappa'],1)
        with self.assertRaises(ValueError):agreement([True],[])
