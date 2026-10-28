"""Explicit Cricsheet JSON ingestion boundary for supported statistical fields."""
from datetime import date
from .scoring import DISMISSALS, NOT_DISMISSED


def normalize_legacy_match(value):
    """Narrow documented normalization, in memory only; return auditable changes."""
    changes = []
    if not isinstance(value, dict) or not isinstance(value.get('innings'), list):
        return changes
    for index, innings in enumerate(value['innings']):
        counts = innings.get('miscounted_overs', {}) if isinstance(innings, dict) else {}
        if not isinstance(counts, dict):
            continue
        for over, count in counts.items():
            if not isinstance(count, dict):
                continue
            balls = count.get('balls')
            if isinstance(balls, str) and balls.isascii() and balls.isdigit() and 1 <= len(balls) <= 2 and int(balls) > 0:
                count['balls'] = int(balls)
                changes.append({'code': 'legacy_miscount_ball_string', 'location': f'innings.{index}.miscounted_overs.{over}.balls'})
    return changes


class SchemaError(ValueError):
    def __init__(self, code, location):
        self.code, self.location = code, location
        super().__init__(code + ' at ' + location)


def fields(value, allowed, required, location):
    if not isinstance(value, dict):
        raise SchemaError('object_required', location)
    if set(value) - set(allowed):
        raise SchemaError('unknown_field', location)
    if set(required) - set(value):
        raise SchemaError('missing_field', location)


def integer(value, location, minimum=0):
    if type(value) is not int or value < minimum:
        raise SchemaError('nonnegative_integer_required', location)


def text(value, location):
    if not isinstance(value, str) or not value.strip() or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise SchemaError('bounded_text_required', location)


def validate_match(value):
    fields(value, ('meta', 'info', 'innings'), ('meta', 'info', 'innings'), 'match')
    fields(value['meta'], ('data_version', 'created', 'revision'), ('data_version',), 'meta')
    if value['meta']['data_version'] not in ('1.0.0', '1.1.0', '1.2.0', '1.3.0'):
        raise SchemaError('unsupported_data_version', 'meta.data_version')
    if 'revision' in value['meta']:
        integer(value['meta']['revision'], 'meta.revision', 1)
    info = value['info']
    fields(info, ('balls_per_over', 'bowl_out', 'dates', 'event', 'gender', 'match_type',
                 'match_type_number', 'missing', 'officials', 'overs', 'player_of_match',
                 'players', 'registry', 'season', 'supersubs', 'team_type', 'teams', 'toss',
                 'venue', 'city', 'outcome'),
           ('balls_per_over', 'dates', 'gender', 'match_type', 'players', 'teams', 'outcome'), 'info')
    integer(info['balls_per_over'], 'info.balls_per_over', 1)
    if info['balls_per_over'] != 6:
        # Legacy summary adapters define economy per six balls. Reject unsupported
        # historical over lengths instead of silently publishing wrong rates.
        raise SchemaError('unsupported_over_length', 'info.balls_per_over')
    if (not isinstance(info['teams'], list) or len(info['teams']) != 2
            or any(not isinstance(team, str) for team in info['teams']) or len(set(info['teams'])) != 2):
        raise SchemaError('two_distinct_teams_required', 'info.teams')
    for team in info['teams']:
        text(team, 'info.teams')
    if not isinstance(info['dates'], list) or not info['dates']:
        raise SchemaError('dates_required', 'info.dates')
    try:
        for item in info['dates']:
            date.fromisoformat(item)
    except (TypeError, ValueError):
        raise SchemaError('invalid_date', 'info.dates') from None
    if info['match_type'] not in ('Test', 'ODI', 'T20', 'IT20', 'T20I'):
        raise SchemaError('unsupported_format', 'info.match_type')
    if not isinstance(info['players'], dict):
        raise SchemaError('object_required', 'info.players')
    for team, players in info['players'].items():
        if team not in info['teams']:
            raise SchemaError('unknown_team', 'info.players')
        if not isinstance(players, list) or len(players) > 50:
            raise SchemaError('bounded_players_array_required', 'info.players')
        for player in players:
            text(player, 'info.players')
    fields(info['outcome'], ('winner', 'by', 'result', 'method', 'eliminator', 'bowl_out'), (), 'info.outcome')
    if info['outcome'].get('winner') is not None and info['outcome']['winner'] not in info['teams']:
        raise SchemaError('unknown_winner', 'info.outcome')
    if info['outcome'].get('result') not in (None, 'tie', 'draw', 'no result'):
        raise SchemaError('unsupported_result', 'info.outcome.result')
    if not isinstance(value['innings'], list) or len(value['innings']) > 20:
        raise SchemaError('bounded_innings_array_required', 'innings')
    for index, innings in enumerate(value['innings']):
        location = 'innings.' + str(index)
        fields(innings, ('team', 'overs', 'declared', 'forfeited', 'absent_hurt', 'penalty_runs',
                        'powerplays', 'miscounted_overs', 'target', 'super_over'), ('team', 'overs'), location)
        if innings['team'] not in info['teams']:
            raise SchemaError('unknown_team', location)
        for flag in ('declared', 'forfeited', 'super_over'):
            if flag in innings and type(innings[flag]) is not bool:
                raise SchemaError('boolean_required', location + '.' + flag)
        if 'penalty_runs' in innings:
            fields(innings['penalty_runs'], ('pre', 'post'), (), location + '.penalty_runs')
            for name, amount in innings['penalty_runs'].items():
                integer(amount, location + '.penalty_runs.' + name)
        if 'target' in innings:
            fields(innings['target'], ('overs', 'runs'), (), location + '.target')
            if 'runs' in innings['target']:
                integer(innings['target']['runs'], location + '.target.runs')
        if 'miscounted_overs' in innings:
            if not isinstance(innings['miscounted_overs'], dict):
                raise SchemaError('object_required', location + '.miscounted_overs')
            for number, count in innings['miscounted_overs'].items():
                if not number.isascii() or not number.isdigit():
                    raise SchemaError('invalid_over_number', location)
                fields(count, ('balls', 'umpire'), ('balls',), location + '.miscounted_overs')
                integer(count['balls'], location + '.miscounted_overs.balls', 1)
        if not isinstance(innings['overs'], list) or len(innings['overs']) > 1000:
            raise SchemaError('bounded_overs_array_required', location)
        dismissed, seen_overs = set(), set()
        for over in innings['overs']:
            fields(over, ('over', 'deliveries'), ('over', 'deliveries'), location + '.over')
            integer(over['over'], location + '.over.number')
            if over['over'] in seen_overs:
                raise SchemaError('duplicate_over', location)
            seen_overs.add(over['over'])
            if not isinstance(over['deliveries'], list) or len(over['deliveries']) > 100:
                raise SchemaError('bounded_deliveries_array_required', location)
            for attempt, delivery in enumerate(over['deliveries']):
                point = location + '.over.' + str(over['over']) + '.attempt.' + str(attempt)
                fields(delivery, ('actual_delivery', 'batter', 'bowler', 'non_striker', 'runs',
                                  'extras', 'wickets', 'replacements', 'review'),
                       ('batter', 'bowler', 'non_striker', 'runs'), point)
                for name in ('batter', 'bowler', 'non_striker'):
                    text(delivery[name], point + '.' + name)
                runs = delivery['runs']
                fields(runs, ('batter', 'extras', 'total', 'non_boundary'), ('batter', 'extras', 'total'), point + '.runs')
                for name in ('batter', 'extras', 'total'):
                    integer(runs[name], point + '.runs.' + name)
                if 'non_boundary' in runs and type(runs['non_boundary']) is not bool:
                    raise SchemaError('boolean_required', point + '.runs.non_boundary')
                extras = delivery.get('extras', {})
                fields(extras, ('byes', 'legbyes', 'noballs', 'penalty', 'wides'), (), point + '.extras')
                for name, amount in extras.items():
                    integer(amount, point + '.extras.' + name, 1)
                if sum(extras.values()) != runs['extras'] or runs['total'] != runs['batter'] + runs['extras']:
                    raise SchemaError('run_conservation', point)
                if extras.get('wides') and extras.get('noballs'):
                    raise SchemaError('wide_and_no_ball_conflict', point)
                wickets = delivery.get('wickets', [])
                if not isinstance(wickets, list):
                    raise SchemaError('array_required', point + '.wickets')
                for wicket in wickets:
                    fields(wicket, ('kind', 'player_out', 'fielders'), ('kind', 'player_out'), point + '.wicket')
                    if not isinstance(wicket['kind'], str) or wicket['kind'] not in DISMISSALS:
                        raise SchemaError('unknown_dismissal', point)
                    text(wicket['player_out'], point + '.player_out')
                    if wicket['player_out'] in dismissed:
                        raise SchemaError('duplicate_dismissal', point)
                    if wicket['kind'] not in NOT_DISMISSED:
                        dismissed.add(wicket['player_out'])
    return value
