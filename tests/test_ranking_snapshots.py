from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from criclytics_app import create_app
from criclytics_app.integrations.ranking_snapshots import parse,publish,read


def authored(first_rating=1000):
    rows = ''.join(f'<tr><td><span>{i}</span><span>2</span></td><td>Authored country</td>'
        f'<td><a><span>Player</span> <span>{i}</span></a></td><td>{first_rating if i==1 else 1000-i}</td>'
        '<td>Authored career best</td></tr>' for i in range(1,11))
    return ("<h2>MEN'S T20I Batting rankings</h2><span>Rank date - 27 October 2020</span>"
        '<table><thead><tr><th>POS</th><th>TEAM</th><th>Player</th><th>Rating</th>'
        '<th>Career Best Rating</th></tr></thead><tbody>'+rows+'</tbody></table>')


class RankingSnapshotTests(unittest.TestCase):
    def test_real_table_shapes_ties_zero_rating_and_team_totals(self):
        tied = authored().replace('<span>2</span><span>2</span>','<span>0=</span><span>2</span>').replace('<td>998</td>','<td>1000</td>')
        result = parse(tied,'batting','T20I','2020-10-28T00:00:00Z')
        self.assertEqual([r['rank'] for r in result['rankings'][:3]],[1,1,3])
        rows = ''.join(f'<tr><td><span>{i}</span></td><td><a>Team {i}</a></td><td>20</td><td>1,000</td><td>{10-i}</td></tr>' for i in range(1,11))
        html = "<h2>MEN'S T20I Team Rankings</h2><p>Rank date - 27 October 2020</p><table><thead><tr><th>POS</th><th>TEAM</th><th>Matches</th><th>PTS</th><th>Rating</th></tr></thead><tbody>"+rows+'</tbody></table>'
        result = parse(html,'teams','T20I','2020-10-28T00:00:00Z')
        self.assertEqual(result['rankings'][-1]['rating'],0)
        self.assertEqual(result['rankings'][0]['points'],1000)

    def test_invalid_refresh_keeps_last_good_and_corrupt_current_uses_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Path(folder)/'rankings.sqlite3'
            first = publish(store,authored(),'batting','T20I','2020-10-28T00:00:00Z')
            unchanged = publish(store,authored(),'batting','T20I','2020-10-29T00:00:00Z')
            self.assertEqual(first['fetched_at'],unchanged['fetched_at'])
            for html in (authored().replace('<th>Rating</th>','<th>Changed</th>'),
                         authored().replace('27 October 2020','30 October 2020'),
                         authored().replace('<span>2</span></a>','<span>1</span></a>'),
                         authored().replace("MEN'S","WOMEN'S")):
                with self.assertRaises(ValueError):
                    publish(store,html,'batting','T20I','2020-10-29T00:00:00Z')
                self.assertEqual(read(store,'batting','T20I')['source_sha256'],first['source_sha256'])
            publish(store,authored(1010),'batting','T20I','2020-10-29T00:00:00Z')
            with closing(sqlite3.connect(store)) as db,db:
                db.execute("UPDATE snapshots SET payload='corrupt' WHERE slot=0")
            backup = read(store,'batting','T20I')
            self.assertTrue(backup['backup_used'])
            self.assertEqual(backup['source_sha256'],first['source_sha256'])
            publish(store,authored(1020),'batting','T20I','2020-10-29T00:00:00Z')
            self.assertFalse(read(store,'batting','T20I')['backup_used'])
            with closing(sqlite3.connect(store)) as db:
                self.assertEqual(json.loads(db.execute('SELECT payload FROM snapshots WHERE slot=1').fetchone()[0])['source_sha256'],first['source_sha256'])
            with self.assertRaises(ValueError):
                parse(authored(),'bowling','T20I','2020-10-29T00:00:00Z')

    def test_personal_snapshot_never_exposed_to_remote_or_cross_origin(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Path(folder)/'rankings.sqlite3'
            publish(store,authored(),'batting','T20I','2020-10-28T00:00:00Z')
            app = create_app({'TESTING':True,'RANKING_SNAPSHOT_STORE':store,
                'PROCESSED_DIR':folder,'LIVE_DIR':folder,'LIVE_FETCH_ENABLED':False,'REDIS_URL':''})
            with app.test_client() as client:
                local = client.get('/api/icc-rankings')
                self.assertEqual(len(local.json['rankings']),10)
                self.assertTrue(local.json['stale'])
                self.assertIn('no-store',local.headers['Cache-Control'])
                for options in ({'environ_overrides':{'REMOTE_ADDR':'192.0.2.1'}},
                                {'headers':{'Host':'public.example'}},
                                {'headers':{'Origin':'https://external.example'}},
                                {'headers':{'Sec-Fetch-Site':'cross-site'}}):
                    response = client.get('/api/icc-rankings',**options)
                    self.assertFalse(response.json['available'])
                    self.assertEqual(response.json['rankings'],[])
                    self.assertIsNone(response.json['fetched_at'])
                self.assertEqual(client.get('/api/icc-rankings?category=invalid').status_code,400)
