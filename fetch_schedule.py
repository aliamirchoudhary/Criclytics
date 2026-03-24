"""
fetch_schedule.py — Cricket Schedule Fetcher
=============================================
Replaces CricAPI for match fixtures when CricAPI is unavailable.
Tries CricAPI first, then falls back to ICC hardcoded 2026 calendar.

Usage:  python fetch_schedule.py
Output: data/live/matches.json, data/live/live.json
"""

import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIVE_DIR = os.path.join(BASE_DIR, "data", "live")
os.makedirs(LIVE_DIR, exist_ok=True)

CRICAPI_KEY  = os.environ.get("CRICAPI_KEY", "")
CRICAPI_BASE = "https://api.cricapi.com/v1"

SENIOR_TEAMS = {
    'India','Australia','England','Pakistan','New Zealand','South Africa',
    'Sri Lanka','Bangladesh','West Indies','Afghanistan','Zimbabwe',
    'Ireland','Scotland','Netherlands','Nepal','UAE','Namibia',
    'Canada','USA','Oman','Papua New Guinea',
}

SKIP_WORDS = ['women','u19','u-19','under-19','under 19',' a vs ',' a match',
              'unofficial','tbc','lions','titans','warriors','dolphins','cobras',
              'qalandars','zalmi','sultans','kings','blasters','eagles',
              'board xi','president xi','emerging']

def http_get(url, timeout=12):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
               'Accept': 'application/json'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print(f"    ✗ {url[:55]}… — {e}")
        return None

def is_senior(teams, name=''):
    if len(teams) < 2: return False
    t1, t2 = teams[0], teams[1]
    combined = (t1 + ' ' + t2 + ' ' + name).lower()
    if any(w in combined for w in SKIP_WORDS): return False
    return t1 in SENIOR_TEAMS or t2 in SENIOR_TEAMS

def norm_cricapi(m):
    teams = m.get('teams', [])
    t1 = teams[0] if teams else ''
    t2 = teams[1] if len(teams) > 1 else ''
    scores = m.get('score', [])
    def fs(s): return f"{s['r']}/{s['w']} ({s['o']}ov)" if s else ''
    mt = m.get('matchType','').upper()
    if mt == 'T20': mt = 'T20I'
    elif mt == 'TEST': mt = 'Test'
    return {
        'id': m.get('id',''), 'name': m.get('name',''),
        'matchType': mt, 'status': m.get('status',''),
        'venue': m.get('venue',''), 'date': m.get('date',''),
        'dateTimeGMT': m.get('dateTimeGMT',''),
        't1': t1, 't2': t2,
        't1s': fs(scores[0]) if scores else '',
        't2s': fs(scores[1]) if len(scores) > 1 else '',
        'matchStarted': m.get('matchStarted', False),
        'matchEnded': m.get('matchEnded', False),
        'series_id': m.get('series_id',''),
    }

# ── ICC 2026 Schedule (hardcoded fallback — always works) ─────────────────────
ICC_2026 = [
    # Completed
    {"id":"nz-sa-t20-2","matchType":"T20I","status":"New Zealand won by 68 runs",
     "venue":"Seddon Park, Hamilton","date":"2026-03-17","dateTimeGMT":"2026-03-17T00:00:00",
     "t1":"New Zealand","t2":"South Africa","t1s":"175/6 (20ov)","t2s":"107/10 (15.3ov)",
     "matchStarted":True,"matchEnded":True,"series_id":"sa-nz-2026",
     "name":"New Zealand vs South Africa, 2nd T20I"},
    {"id":"nz-sa-t20-1","matchType":"T20I","status":"South Africa won by 7 wkts",
     "venue":"Eden Park, Auckland","date":"2026-03-14","dateTimeGMT":"2026-03-14T06:00:00",
     "t1":"New Zealand","t2":"South Africa","t1s":"167/8 (20ov)","t2s":"168/3 (17.2ov)",
     "matchStarted":True,"matchEnded":True,"series_id":"sa-nz-2026",
     "name":"New Zealand vs South Africa, 1st T20I"},
    {"id":"ban-pak-odi-1","matchType":"ODI","status":"Bangladesh won by 11 runs",
     "venue":"Shere Bangla National Stadium, Dhaka","date":"2026-03-16","dateTimeGMT":"2026-03-16T09:00:00",
     "t1":"Bangladesh","t2":"Pakistan","t1s":"298/7 (50ov)","t2s":"287/9 (50ov)",
     "matchStarted":True,"matchEnded":True,"series_id":"ban-pak-2026",
     "name":"Bangladesh vs Pakistan, 1st ODI"},
    # Upcoming NZ vs SA (3rd T20I)
    {"id":"nz-sa-t20-3","matchType":"T20I","status":"Match not started",
     "venue":"Saxton Oval, Nelson","date":"2026-03-21","dateTimeGMT":"2026-03-21T06:00:00",
     "t1":"New Zealand","t2":"South Africa","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"sa-nz-2026",
     "name":"New Zealand vs South Africa, 3rd T20I"},
    # Afghanistan tour of India Jun 2026
    {"id":"ind-afg-test-2026","matchType":"Test","status":"Match not started",
     "venue":"M. Chinnaswamy Stadium, Bengaluru","date":"2026-06-06","dateTimeGMT":"2026-06-06T04:00:00",
     "t1":"India","t2":"Afghanistan","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026",
     "name":"India vs Afghanistan, Only Test"},
    {"id":"ind-afg-odi1-2026","matchType":"ODI","status":"Match not started",
     "venue":"Rajiv Gandhi Int. Stadium, Hyderabad","date":"2026-06-10","dateTimeGMT":"2026-06-10T09:00:00",
     "t1":"India","t2":"Afghanistan","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026",
     "name":"India vs Afghanistan, 1st ODI"},
    {"id":"ind-afg-odi2-2026","matchType":"ODI","status":"Match not started",
     "venue":"JSCA International Stadium, Ranchi","date":"2026-06-13","dateTimeGMT":"2026-06-13T09:00:00",
     "t1":"India","t2":"Afghanistan","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026",
     "name":"India vs Afghanistan, 2nd ODI"},
    {"id":"ind-afg-odi3-2026","matchType":"ODI","status":"Match not started",
     "venue":"Punjab Cricket Association Stadium, Mohali","date":"2026-06-16","dateTimeGMT":"2026-06-16T09:00:00",
     "t1":"India","t2":"Afghanistan","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026",
     "name":"India vs Afghanistan, 3rd ODI"},
    # NZ tour of England Jun 2026
    {"id":"eng-nz-test1-2026","matchType":"Test","status":"Match not started",
     "venue":"Lord's Cricket Ground, London","date":"2026-06-04","dateTimeGMT":"2026-06-04T10:00:00",
     "t1":"England","t2":"New Zealand","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026",
     "name":"England vs New Zealand, 1st Test"},
    {"id":"eng-nz-test2-2026","matchType":"Test","status":"Match not started",
     "venue":"Trent Bridge, Nottingham","date":"2026-06-12","dateTimeGMT":"2026-06-12T10:00:00",
     "t1":"England","t2":"New Zealand","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026",
     "name":"England vs New Zealand, 2nd Test"},
    {"id":"eng-nz-test3-2026","matchType":"Test","status":"Match not started",
     "venue":"Headingley, Leeds","date":"2026-06-25","dateTimeGMT":"2026-06-25T10:00:00",
     "t1":"England","t2":"New Zealand","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026",
     "name":"England vs New Zealand, 3rd Test"},
    # India tour of England Jul 2026
    {"id":"eng-ind-t20-1-2026","matchType":"T20I","status":"Match not started",
     "venue":"Edgbaston, Birmingham","date":"2026-07-01","dateTimeGMT":"2026-07-01T17:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 1st T20I"},
    {"id":"eng-ind-t20-2-2026","matchType":"T20I","status":"Match not started",
     "venue":"Lord's Cricket Ground, London","date":"2026-07-04","dateTimeGMT":"2026-07-04T17:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 2nd T20I"},
    {"id":"eng-ind-t20-3-2026","matchType":"T20I","status":"Match not started",
     "venue":"The Oval, London","date":"2026-07-07","dateTimeGMT":"2026-07-07T17:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 3rd T20I"},
    {"id":"eng-ind-t20-4-2026","matchType":"T20I","status":"Match not started",
     "venue":"Old Trafford, Manchester","date":"2026-07-11","dateTimeGMT":"2026-07-11T17:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 4th T20I"},
    {"id":"eng-ind-t20-5-2026","matchType":"T20I","status":"Match not started",
     "venue":"Sophia Gardens, Cardiff","date":"2026-07-14","dateTimeGMT":"2026-07-14T17:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 5th T20I"},
    {"id":"eng-ind-odi-1-2026","matchType":"ODI","status":"Match not started",
     "venue":"Headingley, Leeds","date":"2026-07-17","dateTimeGMT":"2026-07-17T10:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 1st ODI"},
    {"id":"eng-ind-odi-2-2026","matchType":"ODI","status":"Match not started",
     "venue":"Bristol County Ground","date":"2026-07-20","dateTimeGMT":"2026-07-20T10:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 2nd ODI"},
    {"id":"eng-ind-odi-3-2026","matchType":"ODI","status":"Match not started",
     "venue":"Trent Bridge, Nottingham","date":"2026-07-23","dateTimeGMT":"2026-07-23T10:30:00",
     "t1":"England","t2":"India","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026",
     "name":"England vs India, 3rd ODI"},
    # Australia tour of South Africa Sep 2026
    {"id":"sa-aus-test1-2026","matchType":"Test","status":"Match not started",
     "venue":"Newlands, Cape Town","date":"2026-09-24","dateTimeGMT":"2026-09-24T08:00:00",
     "t1":"South Africa","t2":"Australia","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"aus-sa-2026",
     "name":"South Africa vs Australia, 1st Test"},
    {"id":"sa-aus-test2-2026","matchType":"Test","status":"Match not started",
     "venue":"St George's Park, Gqeberha","date":"2026-10-02","dateTimeGMT":"2026-10-02T08:00:00",
     "t1":"South Africa","t2":"Australia","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"aus-sa-2026",
     "name":"South Africa vs Australia, 2nd Test"},
    {"id":"sa-aus-odi1-2026","matchType":"ODI","status":"Match not started",
     "venue":"Wanderers, Johannesburg","date":"2026-10-10","dateTimeGMT":"2026-10-10T11:00:00",
     "t1":"South Africa","t2":"Australia","t1s":"","t2s":"",
     "matchStarted":False,"matchEnded":False,"series_id":"aus-sa-2026",
     "name":"South Africa vs Australia, 1st ODI"},
]

def try_cricapi():
    """Try CricAPI. Returns (live_list, completed_list, upcoming_list) or None."""
    print("  Trying CricAPI live endpoint...")
    data = http_get(f"{CRICAPI_BASE}/currentMatches?apikey={CRICAPI_KEY}&offset=0")
    if not data or data.get('status') != 'success':
        print("  CricAPI failed or blocked.")
        return None, None, None

    raw = data.get('data', [])
    good = [m for m in raw if is_senior(m.get('teams',[]), m.get('name',''))]
    print(f"  CricAPI: {len(raw)} total, {len(good)} senior international")

    time.sleep(1)
    fix_data = http_get(f"{CRICAPI_BASE}/matches?apikey={CRICAPI_KEY}&offset=0")
    fix_raw  = (fix_data or {}).get('data', []) if fix_data else []
    fix_good = [m for m in fix_raw if is_senior(m.get('teams',[]), m.get('name',''))]

    live_l, comp_l, up_l = [], [], []
    for m in good:
        n = norm_cricapi(m)
        if n['matchStarted'] and not n['matchEnded']:  live_l.append(n)
        elif n['matchEnded']:                          comp_l.append(n)
        else:                                          up_l.append(n)
    for m in fix_good:
        n = norm_cricapi(m)
        if not n['matchStarted']: up_l.append(n)

    return live_l, comp_l, up_l

def main():
    print("=" * 55)
    print("  Criclytics — Match Schedule Fetcher")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    live_matches = []
    completed    = []
    upcoming     = []
    source       = "icc_calendar"

    # ── Try CricAPI ───────────────────────────────────────────────
    lv, cm, up = try_cricapi()
    if lv is not None:   # CricAPI succeeded
        live_matches = lv
        completed    = cm
        upcoming     = up
        source       = "cricapi"
        print(f"  CricAPI OK → Live:{len(lv)} Completed:{len(cm)} Upcoming:{len(up)}")
    else:
        print("  CricAPI unavailable — using ICC 2026 calendar fallback")

    # ── Always merge ICC calendar ─────────────────────────────────
    # Use ICC calendar for any gaps (upcoming always)
    existing_ids = {m['id'] for m in live_matches + completed + upcoming}
    for m in ICC_2026:
        if m['id'] not in existing_ids:
            if m['matchEnded']:
                completed.append(m)
            elif m['matchStarted']:
                live_matches.append(m)
            else:
                upcoming.append(m)
            existing_ids.add(m['id'])

    # ── Sort ──────────────────────────────────────────────────────
    upcoming_s  = sorted(upcoming,     key=lambda x: x.get('date',''))
    completed_s = sorted(completed,    key=lambda x: x.get('date',''), reverse=True)
    final       = live_matches + upcoming_s + completed_s

    # ── Write matches.json ────────────────────────────────────────
    path = os.path.join(LIVE_DIR, "matches.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({"data": final,
                   "fetched_at": datetime.now(timezone.utc).isoformat(),
                   "source": source}, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ matches.json — {len(final)} matches "
          f"(Live:{len(live_matches)} Upcoming:{len(upcoming_s)} Completed:{len(completed_s)})")

    # ── Write live.json ───────────────────────────────────────────
    path2 = os.path.join(LIVE_DIR, "live.json")
    with open(path2, 'w', encoding='utf-8') as f:
        json.dump({"data": live_matches,
                   "fetched_at": datetime.now(timezone.utc).isoformat(),
                   "source": source}, f, indent=2, ensure_ascii=False)
    print(f"  ✓ live.json — {len(live_matches)} live matches")

    print("\n" + "=" * 55)
    print("  Done. Restart Flask to serve updated data.")
    print("=" * 55)

if __name__ == "__main__":
    main()
