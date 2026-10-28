"""Version 2 innings scoring. See docs/SCORING_CONTRACT.md for conventions."""
from collections import defaultdict

BOWLER_WICKETS = {'bowled', 'caught', 'caught and bowled', 'lbw', 'stumped', 'hit wicket'}
NOT_DISMISSED = {'retired hurt', 'retired not out'}
DISMISSALS = BOWLER_WICKETS | NOT_DISMISSED | {'run out', 'retired out', 'obstructing the field',
                                             'hit the ball twice', 'handled the ball', 'timed out'}


def overs(balls, balls_per_over=6):
    return f'{balls // balls_per_over}.{balls % balls_per_over}'


def score_innings(innings, index, balls_per_over=6, fmt='T20I'):
    batting, bowling = {}, {}
    penalty_runs = innings.get('penalty_runs') or {}
    total = penalty_runs.get('pre', 0)
    legal, wickets, boundaries, dots = 0, 0, 0, 0
    fall, partnerships = [], []
    phases = defaultdict(lambda: {'runs': 0, 'wickets': 0, 'attempts': 0})
    partnership_runs = 0

    def batter_row(name):
        if name and name not in batting:
            batting[name] = {'batsman': name, 'r': 0, 'b': 0, '4s': 0, '6s': 0,
                             'dismissed': False, 'dismissal': 'not out', 'order': len(batting) + 1}
        return batting.get(name)

    for over in innings.get('overs', []):
        over_number = over['over']
        over_bowlers = defaultdict(lambda: {'runs': 0, 'balls': 0})
        for delivery in over.get('deliveries', []):
            name, bowler = delivery['batter'], delivery['bowler']
            striker = batter_row(name)
            batter_row(delivery.get('non_striker'))
            row = bowling.setdefault(bowler, {'bowler': bowler, 'r': 0, 'w': 0, 'balls': 0,
                                              'm': 0, 'wd': 0, 'nb': 0})
            runs, extras = delivery['runs'], delivery.get('extras', {})
            bat_runs, delivery_total = runs['batter'], runs['total']
            if delivery_total != bat_runs + sum(extras.values()):
                raise ValueError('Delivery run conservation failure')
            wides, noballs = extras.get('wides', 0), extras.get('noballs', 0)
            is_legal = not wides and not noballs
            legal += int(is_legal)
            total += delivery_total
            partnership_runs += delivery_total
            striker['r'] += bat_runs
            striker['b'] += int(not wides)  # Delivered no-ball counts as faced, not as legal.
            if not runs.get('non_boundary') and bat_runs in (4, 6):
                striker[str(bat_runs) + 's'] += 1
                boundaries += 1
            dots += int(is_legal and delivery_total == 0)
            conceded = bat_runs + wides + noballs
            row['r'] += conceded
            row['balls'] += int(is_legal)
            row['wd'] += wides
            row['nb'] += noballs
            over_bowlers[bowler]['runs'] += conceded
            over_bowlers[bowler]['balls'] += int(is_legal)
            delivery_wickets = 0
            for wicket in delivery.get('wickets', []):
                kind = wicket['kind']
                if kind not in DISMISSALS:
                    raise ValueError('Unsupported dismissal kind')
                dismissed = batter_row(wicket['player_out'])
                dismissed['dismissal'] = kind
                if kind not in NOT_DISMISSED:
                    dismissed['dismissed'] = True
                    wickets += 1
                    delivery_wickets += 1
                    if kind in BOWLER_WICKETS:
                        row['w'] += 1
                    fall.append(f"{total}/{wickets} ({wicket['player_out']}, {overs(legal, balls_per_over)} ov)")
                    partnerships.append({'innings': index + 1, 'team': innings['team'], 'wicket_no': wickets,
                        'names': ' & '.join(filter(None, [name, delivery.get('non_striker')])),
                        'runs': partnership_runs, 'score': total})
                    partnership_runs = 0
            if fmt == 'T20I':
                phase = 'powerplay' if over_number < 6 else 'middle' if over_number < 15 else 'death'
                phases[phase]['runs'] += delivery_total
                phases[phase]['wickets'] += delivery_wickets
                phases[phase]['attempts'] += 1
        expected = innings.get('miscounted_overs', {}).get(str(over_number), {}).get('balls', balls_per_over)
        if isinstance(expected, str) and expected.isascii() and expected.isdigit() and len(expected) <= 2:
            expected = int(expected)
        if len(over_bowlers) == 1:
            bowler, counts = next(iter(over_bowlers.items()))
            if counts['balls'] == expected and counts['runs'] == 0:
                bowling[bowler]['m'] += 1
    total += penalty_runs.get('post', 0)
    for row in batting.values():
        row['sr'] = round(row['r'] * 100 / row['b'], 2) if row['b'] else None
    for row in bowling.values():
        row['o'] = overs(row['balls'], balls_per_over)
        row['eco'] = round(row['r'] * balls_per_over / row['balls'], 2) if row['balls'] else None
    return {'innings_id': index + 1, 'team': innings['team'], 'super_over': bool(innings.get('super_over')),
            'batting': list(batting.values()), 'bowling': list(bowling.values()),
            'total': total, 'wickets': wickets, 'legal_balls': legal, 'overs': overs(legal, balls_per_over),
            'boundaries': boundaries, 'dot_balls': dots, 'phases': dict(phases),
            'fall_of_wickets': fall, 'partnerships': partnerships}


def score_match(match):
    info = match['info']
    fmt = match.get('_format') or info.get('match_type')
    if fmt in ('T20', 'IT20'):
        fmt = 'T20I'
    innings = [score_innings(inn, index, info.get('balls_per_over', 6), fmt)
               for index, inn in enumerate(match.get('innings', []))]
    regular = [inn for inn in innings if not inn['super_over']]
    batters = [(r, inn) for inn in regular for r in inn['batting']]
    bowlers = [(r, inn) for inn in regular for r in inn['bowling']]
    top = max(batters, key=lambda pair: pair[0]['r'], default=None)
    best = max(bowlers, key=lambda pair: (pair[0]['w'], -pair[0]['r']), default=None)
    return {'innings': innings, 'partnerships': [p for inn in regular for p in inn['partnerships']],
            'match_stats': {'top_scorer': {'name': top[0]['batsman'], 'runs': top[0]['r'], 'team': top[1]['team']} if top else None,
                            'best_bowler': {'name': best[0]['bowler'], 'wickets': best[0]['w'], 'runs': best[0]['r'],
                                            'overs': best[0]['o']} if best else None,
                            'innings': [{'boundaries': i['boundaries'], 'dot_balls': i['dot_balls']} for i in innings]}}
