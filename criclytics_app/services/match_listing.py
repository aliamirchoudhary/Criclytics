"""Bounded public fixture summaries; scorecards belong to detail routes."""
from werkzeug.exceptions import BadRequest

FIELDS = ('id', 'unique_id', 'name', 't1', 't2', 't1s', 't2s', 'teams',
          'team1', 'team2', 'matchType', 'date', 'dateTimeGMT', 'venue',
          'series', 'series_id', 'status', 'matchStarted', 'matchEnded')
ALIASES = {'rsa': 'south africa', 'sa': 'south africa', 'pak': 'pakistan',
           'ind': 'india', 'eng': 'england', 'aus': 'australia',
           'nz': 'new zealand', 'wi': 'west indies', 'sl': 'sri lanka'}


def team_key(value):
    value = str(value or '').strip().casefold()
    return ALIASES.get(value, value)


def summary(match, completed=False):
    result = {key: match[key] for key in FIELDS if key in match}
    result['id'] = str(match.get('id') or match.get('unique_id') or '')
    result['teams'] = (match.get('teams') or [match.get('t1') or match.get('team1', ''),
                                           match.get('t2') or match.get('team2', '')])[:2]
    for index in (0, 1):
        result.setdefault('t' + str(index + 1), result['teams'][index] if len(result['teams']) > index else '')
    if isinstance(match.get('score'), list):
        result['score'] = [{k: s[k] for k in ('r', 'w', 'o', 'inning') if k in s}
                           for s in match['score'][:4] if isinstance(s, dict)]
    result['matchEnded'] = completed or bool(match.get('matchEnded'))
    result['matchStarted'] = result['matchEnded'] or bool(match.get('matchStarted'))
    result['listingStatus'] = ('completed' if result['matchEnded'] else
                               'live' if result['matchStarted'] else 'upcoming')
    return result


def listing(live, completed, args, identities=None):
    status = args.get('status', 'all')
    order = args.get('sort', 'newest')
    if status not in ('all', 'upcoming', 'live', 'completed'):
        raise BadRequest('Unsupported match status')
    if order not in ('newest', 'oldest', 'format'):
        raise BadRequest('Unsupported match sort')
    rows = {}
    # Exact IDs only: do not merge unrelated matches using fuzzy names/dates.
    for source, ended in ((completed, True), (live, False)):
        for match in source:
            item = summary(match, ended)
            if item['id']:
                canonical = identities.match(item['id'], 'cricsheet' if ended else 'cricapi') if identities else None
                if canonical:item['identity_id']=canonical
                identity_key = canonical or item['id']
                if identity_key not in rows:rows[identity_key]=item
                elif not canonical:rows[identity_key]=item
                if canonical:
                    refs=rows[identity_key].setdefault('source_refs',[])
                    ref={'provider':'cricsheet' if ended else 'cricapi','id':item['id']}
                    if ref not in refs:refs.append(ref)
    values = list(rows.values())
    if status != 'all':
        values = [m for m in values if m['listingStatus'] == status]
    fmt = args.get('format', '').casefold().replace('t20i', 't20')
    if fmt:
        values = [m for m in values if str(m.get('matchType', '')).casefold().replace('t20i', 't20') == fmt]
    if args.get('competition') == 'ipl':
        values = [m for m in values if 'indian premier league' in str(m.get('series', '')).casefold()
                  or 'ipl' in str(m.get('series', '')).casefold().split()]
    team = team_key(args.get('team'))
    if team:
        values = [m for m in values if team in [team_key(t) for t in m['teams']]]
    venue = args.get('venue', '').casefold()
    if venue:
        values = [m for m in values if str(m.get('venue', '')).casefold() == venue]
    date = args.get('date', '')
    if date:
        values = [m for m in values if str(m.get('date', '')).startswith(date)]
    values.sort(key=lambda m: (str(m.get('dateTimeGMT') or m.get('date') or ''), m['id']),
                reverse=order != 'oldest')
    if order == 'format':
        values.sort(key=lambda m: str(m.get('matchType', '')).casefold())
    limit = int(args.get('limit', 20))
    offset = int(args.get('offset', 0))
    total = len(values)
    return {'data': values[offset:offset + limit], 'pagination':
            {'total': total, 'limit': limit, 'offset': offset,
             'has_more': offset + limit < total}}
