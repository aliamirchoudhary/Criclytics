"""Conservative observation metadata: unknown timestamps never become now."""
from copy import deepcopy
from datetime import datetime, timezone


def metadata(data, now=None, max_age_seconds=86400):
    data = data or {}
    source = str(data.get('source') or 'unknown')
    fallback = bool(data.get('fallback')) or any(word in source.lower() for word in
                ('hardcoded', 'fallback', 'calendar', 'sample', 'unknown'))
    effective = data.get('effective_date')
    fetched = data.get('fetched_at') or data.get('scraped_at')
    if source == 'hardcoded_april_2026':
        effective, fetched = '2026-04', None
    now = now or datetime.now(timezone.utc)
    stale = True
    if fetched and not fallback:
        try:
            stamp = datetime.fromisoformat(fetched.replace('Z', '+00:00'))
            if stamp.tzinfo is not None:
                age = (now - stamp).total_seconds()
                stale = age < 0 or age > max_age_seconds
                if effective:
                    effective_stamp = datetime.fromisoformat(str(effective).replace('Z', '+00:00'))
                    effective_stamp = effective_stamp.replace(tzinfo=effective_stamp.tzinfo or timezone.utc)
                    stale = stale or (now - effective_stamp).total_seconds() > max_age_seconds + 86400
        except (ValueError, TypeError):
            stale = True
    return {'source': source, 'effective_date': effective, 'fetched_at': fetched,
            'fallback': fallback, 'stale': stale}


def merge_rankings(previous, incoming, info):
    """Publish only nonempty categories; carried categories keep original metadata."""
    result = deepcopy(previous or {'player': {}, 'team': {}})
    result.setdefault('category_metadata', {})
    for category in ('teams', 'batting', 'bowling', 'allrounder'):
        for fmt in ('Test', 'ODI', 'T20I'):
            key = category + ':' + fmt
            if category == 'teams':
                rows = incoming.get('team', {}).get(fmt)
                target = result.setdefault('team', {})
            else:
                rows = incoming.get('player', {}).get(category, {}).get(fmt)
                target = result.setdefault('player', {}).setdefault(category, {})
            if isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows):
                target[fmt] = deepcopy(rows)
                result['category_metadata'][key] = deepcopy(info)
            elif key not in result['category_metadata']:
                result['category_metadata'][key] = metadata(previous)
    # Do not advance global observation timestamps on a partial refresh.
    result['source'] = 'category_snapshots'
    return result
