from copy import deepcopy
import unittest

from criclytics_app.pipeline.scoring import score_match
from criclytics_app.pipeline.cricsheet import build_raw_accumulators, build_players_index, build_h2h


def delivery(runs=0, extras=None, wickets=None):
    extras = extras or {}
    value = {'batter': 'A', 'non_striker': 'B', 'bowler': 'X',
             'runs': {'batter': runs, 'total': runs + sum(extras.values()), 'extras': sum(extras.values())}}
    if extras:
        value['extras'] = extras
    if wickets:
        value['wickets'] = wickets
    return value


def match(innings, fmt='Test'):
    return {'_file': 'hand.json', '_format': fmt, 'info': {'dates': ['2020-01-01'],
            'teams': ['Team A', 'Team X'], 'players': {'Team A': ['A', 'B'], 'Team X': ['X']},
            'venue': 'Ground', 'gender': 'male', 'team_type': 'international',
            'balls_per_over': 6, 'match_type': fmt, 'outcome': {'result': 'draw'}}, 'innings': innings}


class ScoringTests(unittest.TestCase):
    def test_extras_balls_and_non_striker_dismissal(self):
        innings = {'team': 'Team A', 'overs': [{'over': 0, 'deliveries': [
            delivery(extras={'wides': 1}), delivery(4, {'noballs': 1}), delivery(extras={'byes': 2}),
            delivery(extras={'legbyes': 1}), delivery(),
            delivery(1, wickets=[{'kind': 'run out', 'player_out': 'B'}])]}]}
        value = score_match(match([innings]))['innings'][0]
        bats = {r['batsman']: r for r in value['batting']}
        self.assertEqual((value['total'], value['legal_balls'], value['wickets']), (10, 4, 1))
        self.assertEqual((bats['A']['r'], bats['A']['b']), (5, 5))
        self.assertFalse(bats['A']['dismissed'])
        self.assertTrue(bats['B']['dismissed'])
        self.assertEqual((value['bowling'][0]['r'], value['bowling'][0]['w']), (7, 0))

    def test_two_test_innings_milestones_and_maiden_identity(self):
        first = {'team': 'Team A', 'overs': [{'over': 0, 'deliveries': [delivery(6) for _ in range(10)]}]}
        second = deepcopy(first)
        second['overs'][0]['deliveries'] = [delivery(5) for _ in range(11)]
        data = match([first, second])
        stats = build_raw_accumulators([data])
        player = build_players_index(stats['bat'], stats['bowl'])['A']['batting']['Test']
        self.assertEqual((player['innings'], player['highest'], player['fifties'], player['hundreds']), (2, 60, 2, 0))
        self.assertEqual(player['not_outs'], 2)
        self.assertIsNone(player['average'])
        self.assertEqual(build_h2h(stats['h2h_data'])['Team A|Team X|Test']['draws'], 1)
        maiden = {'team': 'Team A', 'overs': [{'over': 0, 'deliveries': [delivery() for _ in range(6)]}]}
        stats = build_raw_accumulators([match([maiden, deepcopy(maiden)])])
        self.assertEqual((stats['bowl'][('X', 'Test')]['innings'], stats['bowl'][('X', 'Test')]['maidens']), (2, 2))

    def test_retirement_credit_superover_and_zero_phases(self):
        innings = {'team': 'Team A', 'overs': [{'over': 0, 'deliveries': [
            delivery(wickets=[{'kind': 'retired hurt', 'player_out': 'B'}]),
            delivery(wickets=[{'kind': 'timed out', 'player_out': 'C'}]),
            delivery(wickets=[{'kind': 'bowled', 'player_out': 'A'}])]}]}
        data = match([innings], 'T20I')
        extra = deepcopy(innings)
        extra['super_over'] = True
        extra['overs'][0]['deliveries'] = [delivery(6)]
        data['innings'].append(extra)
        scored = score_match(data)['innings'][0]
        self.assertEqual(scored['wickets'], 2)
        self.assertEqual(scored['bowling'][0]['w'], 1)
        stats = build_raw_accumulators([data])
        self.assertEqual(stats['bat'][('A', 'T20I')]['runs'], 0)
        self.assertEqual(stats['venue_data']['Ground']['powerplay_runs'], [0])

    def test_incomplete_and_mixed_bowler_overs_are_not_maidens(self):
        innings = {'team': 'Team A', 'overs': [{'over': 0, 'deliveries': [delivery() for _ in range(5)]}]}
        self.assertEqual(score_match(match([innings]))['innings'][0]['bowling'][0]['m'], 0)
        innings['miscounted_overs'] = {'0': {'balls': 5}}
        self.assertEqual(score_match(match([innings]))['innings'][0]['bowling'][0]['m'], 1)
        innings['miscounted_overs'] = {}
        innings['overs'][0]['deliveries'].append(delivery())
        innings['overs'][0]['deliveries'][-1]['bowler'] = 'Y'
        self.assertEqual(sum(row['m'] for row in score_match(match([innings]))['innings'][0]['bowling']), 0)

    def test_bowling_figures_penalty_runs_and_boundary_overthrows(self):
        wickets = []
        for index in range(5):
            name = 'A' + str(index)
            value = delivery(wickets=[{'kind': 'bowled', 'player_out': name}])
            value['batter'] = name
            wickets.append(value)
        four = delivery(4)
        four['runs']['non_boundary'] = True
        innings = {'team': 'Team A', 'penalty_runs': {'before': 5, 'after': 5},
                   'overs': [{'over': 0, 'deliveries': wickets + [four]}]}
        value = score_match(match([innings]))['innings'][0]
        self.assertEqual(value['total'], 14)
        self.assertTrue(value['fall_of_wickets'][0].startswith('5/1'))
        self.assertEqual(value['boundaries'], 0)
        stats = build_raw_accumulators([match([innings])])['bowl'][('X', 'Test')]
        self.assertEqual((stats['best_wkts'], stats['best_runs'], stats['five_wkts']), (5, 4, 1))
