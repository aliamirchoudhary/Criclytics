"""Populate legacy-shaped output tables from explicit innings identities."""
from .scoring import score_match


def aggregate(matches, tables):
    bat, bowl = tables['bat'], tables['bowl']
    for match in sorted(matches, key=lambda m: (str(m['info'].get('dates', [''])[0]), m['_file'])):
        info = match['info']
        fmt, mid = match['_format'], match['_file']
        venue, teams = info.get('venue', 'Unknown Venue'), info.get('teams', [])
        year = int(str(info['dates'][0])[:4])
        outcome = info.get('outcome', {})
        winner = outcome.get('winner')
        result = outcome.get('result')
        v = tables['venue_data'][venue]
        v['matches'] += 1
        v['formats'].add(fmt)
        toss = info.get('toss', {}).get('winner')
        if toss and winner:
            v['toss_total'] += 1
            v['toss_winner_won'] += int(toss == winner)
        for team, players in info.get('players', {}).items():
            for player in players:
                tables['player_country'].setdefault(player, team)
        if len(teams) == 2:
            a, b = sorted(teams)
            h = tables['h2h_data'][(a, b, fmt)]
            h['matches'] += 1
            if result in ('draw', 'tie', 'no result'):
                h[{'draw': 'draws', 'tie': 'ties', 'no result': 'no_result'}[result]] += 1
            elif winner:
                h['team_a_wins' if winner == a else 'team_b_wins'] += 1
            else:
                h['no_result'] += 1
            if str(info['dates'][0]) >= h.get('last_date', ''):
                h['last_result'] = result or (winner + ' won' if winner else 'no result')
                h['last_date'] = str(info['dates'][0])
        for team in teams:
            field = ('drawn' if result == 'draw' else 'tied' if result == 'tie' else
                     'nr' if result == 'no result' or not winner else 'won' if winner == team else 'lost')
            for stats in (tables['team_fmt'][(team, fmt)], tables['team_venue'][(team, fmt, venue)]):
                stats['matches'] += 1
                stats[field] = stats.get(field, 0) + 1
        view = match.get('_scored') or score_match(match)
        innings = [inn for inn in view['innings'] if not inn['super_over']]
        if fmt != 'Test' and len(innings) == 2 and winner and result != 'tie':
            v['chase_results'].append(winner == innings[1]['team'])
            v.setdefault('chase_by_format', {}).setdefault(fmt, []).append(winner == innings[1]['team'])
        for index, inn in enumerate(innings):
            team = inn['team']
            opposition = next((t for t in teams if t != team), '')
            v['innings'].append({'total': inn['total'], 'wickets': inn['wickets'],
                'overs': inn['overs'], 'format': fmt, 'batting_first': index == 0,
                'innings_id': inn['innings_id']})
            ts = tables['team_fmt'][(team, fmt)]
            ts['total_runs'] += inn['total']
            ts['total_innings'] += 1
            ts['total_wkts'] += inn['wickets']
            tv = tables['team_venue'][(team, fmt, venue)]
            tv['total_runs'] += inn['total']
            tv['innings_count'] += 1
            tv['highest'] = max(tv['highest'], inn['total'])
            for phase, phase_stats in inn['phases'].items():
                v[phase + '_runs'].append(phase_stats['runs'])
                v[phase + '_wkts'].append(phase_stats['wickets'])
            for row in inn['batting']:
                player, runs = row['batsman'], row['r']
                groups = [bat[(player, fmt)], tables['bat_vs'][(player, fmt, opposition)],
                          tables['bat_venue'][(player, fmt, venue)], tables['bat_year'][(player, fmt, year)]]
                for stats in groups:
                    stats['innings'] += 1
                    stats['runs'] += runs
                    stats['balls'] += row['b']
                    stats['dismissals'] += int(row['dismissed'])
                    stats['hundreds'] += int(runs >= 100)
                    stats['fifties'] += int(50 <= runs < 100)
                    if 'highest' in stats:
                        stats['highest'] = max(stats['highest'], runs)
                    if 'matches' in stats:
                        stats['matches'].add(mid)
                main = groups[0]
                main['not_outs'] += int(not row['dismissed'])
                main['fours'] += row['4s']
                main['sixes'] += row['6s']
                main['innings_scores'].append(runs)
                main.setdefault('form_events', []).append((str(info['dates'][0]), mid, inn['innings_id'], runs))
                vs = tables['venue_bat'][(venue, player)]
                vs['matches'].add(mid)
                vs['runs'] += runs
                vs['balls'] += row['b']
                vs['dismissals'] += int(row['dismissed'])
                vs['hundreds'] += int(runs >= 100)
                vs['highest'] = max(vs['highest'], runs)
            for row in inn['bowling']:
                player = row['bowler']
                main = bowl[(player, fmt)]
                vs = tables['venue_bowl'][(venue, player)]
                for stats in (main, vs):
                    stats['matches'].add(mid)
                    stats['balls'] += row['balls']
                    stats['runs'] += row['r']
                    stats['wickets'] += row['w']
                    if (row['w'], -row['r']) > (stats['best_wkts'], -stats['best_runs']):
                        stats['best_wkts'], stats['best_runs'] = row['w'], row['r']
                main['innings'] += 1
                main['maidens'] += row['m']
                main['five_wkts'] += int(row['w'] >= 5)
                main['innings_wickets'].append(row['w'])
        # Wicket-type distribution counts dismissals, not retired-hurt events.
        for inning in match.get('innings', []):
            if inning.get('super_over'):
                continue
            for over in inning.get('overs', []):
                for delivery in over.get('deliveries', []):
                    for wicket in delivery.get('wickets', []):
                        if wicket['kind'] not in ('retired hurt', 'retired not out'):
                            v['wicket_kinds'][wicket['kind']] += 1
    return {key: tables[key] for key in ('bat', 'bowl', 'bat_vs', 'bat_venue', 'bat_year', 'venue_data',
            'h2h_data', 'team_fmt', 'team_venue', 'venue_bat', 'venue_bowl', 'player_country')}
