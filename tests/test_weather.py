from copy import deepcopy
import unittest
from criclytics_app.services.weather import WeatherCache,local_to_utc,validate_record
from criclytics_app.integrations.source_policy import source_allowed

LOCATION={'venue_id':'venue:fictional','latitude':24,'longitude':67,'timezone':'Asia/Karachi','source':'fictional fixture','known_at':'2020-01-01T00:00:00Z'}
RECORD={'schema_version':1,'kind':'forecast','source':'fictional observer','license':'fixture-only','venue_id':'venue:fictional',
        'issued_at':'2020-01-01T10:00:00Z','observed_at':'2020-01-01T10:01:00Z','valid_from':'2020-01-01T10:00:00Z','valid_until':'2020-01-01T12:00:00Z',
        'resolution_minutes':60,'values':{'temperature_c':40,'rain_mm_hour':0}}


class WeatherTests(unittest.TestCase):
    def test_timezone_and_dst_ambiguity(self):
        self.assertEqual(local_to_utc('2020-01-01T15:00:00','Asia/Karachi'),'2020-01-01T10:00:00+00:00')
        with self.assertRaises(ValueError):local_to_utc('2020-11-01T01:30:00','America/New_York')
        with self.assertRaises(ValueError):local_to_utc('2020-03-08T02:30:00','America/New_York',0)
        self.assertNotEqual(local_to_utc('2020-11-01T01:30:00','America/New_York',0),local_to_utc('2020-11-01T01:30:00','America/New_York',1))

    def test_late_issue_observation_reanalysis_and_missing_context(self):
        cache=WeatherCache(2);cache.add(RECORD)
        self.assertFalse(cache.select(LOCATION,'2020-01-01T10:00:30Z')['available'])
        got=cache.select(LOCATION,'2020-01-01T11:00:00Z');self.assertTrue(got['available']);self.assertEqual(got['values']['rain_mm_hour'],0)
        self.assertIsNone(got['values']['wind_ms'])
        late=deepcopy(RECORD);late['issued_at']='2020-01-01T11:30:00Z';late['observed_at']='2020-01-01T11:31:00Z';late['values']['temperature_c']=45
        cache.add(late);self.assertEqual(cache.select(LOCATION,'2020-01-01T11:00:00Z')['values']['temperature_c'],40)
        reanalysis=deepcopy(RECORD);reanalysis['kind']='reanalysis';cache.add(reanalysis)
        self.assertFalse(cache.select(LOCATION,'2020-01-01T11:00:00Z')['available'])
        self.assertFalse(cache.select(None,None)['available']);self.assertFalse(source_allowed('open-meteo'))
        bad=deepcopy(RECORD);bad['values']['relative_humidity_pct']=101
        with self.assertRaises(ValueError):validate_record(bad)
        self.assertEqual(len(cache.records),2)
