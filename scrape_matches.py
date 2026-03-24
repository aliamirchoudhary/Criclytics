"""
scrape_matches.py
=================
Cricklytics — Weekly Match Scraper
Fetches men's international schedules + scorecards.

Sources (in order of preference):
  1. Cricbuzz RapidAPI  — live, recent, upcoming + scorecards
  2. Cricsheet raw JSON — historical scorecards from local files
  3. ICC calendar       — fallback schedule

Usage:
    python scrape_matches.py

Run once a week (or after any match completes).
"""

import json, os, time, glob, re
from datetime import datetime, timezone
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LIVE_DIR  = os.path.join(BASE_DIR, "data", "live")
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(LIVE_DIR, exist_ok=True)

RAPIDAPI_KEY  = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
RAPIDAPI_BASE = "https://cricbuzz-cricket.p.rapidapi.com"
HEADERS = {"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": RAPIDAPI_HOST}

SKIP_SERIES = ["qualifier","sub regional","sub-regional","associate","affiliate"]
TEAM_NORM = {
    "India":"India","Australia":"Australia","England":"England","Pakistan":"Pakistan",
    "South Africa":"South Africa","New Zealand":"New Zealand","West Indies":"West Indies",
    "Sri Lanka":"Sri Lanka","Bangladesh":"Bangladesh","Afghanistan":"Afghanistan",
    "Zimbabwe":"Zimbabwe","Ireland":"Ireland","Scotland":"Scotland","Netherlands":"Netherlands",
    "UAE":"UAE","Oman":"Oman","Nepal":"Nepal","Namibia":"Namibia",
    "NZ":"New Zealand","SA":"South Africa","WI":"West Indies","SL":"Sri Lanka",
    "BAN":"Bangladesh","AFG":"Afghanistan","IND":"India","AUS":"Australia",
    "ENG":"England","PAK":"Pakistan","ZIM":"Zimbabwe","IRE":"Ireland",
}

def norm(name): return TEAM_NORM.get(name, name)

def ms_to_date(ms):
    try: return datetime.fromtimestamp(int(ms)/1000).strftime("%Y-%m-%d")
    except: return str(ms)[:10]

def api_get(path, params=None):
    if not HAS_REQUESTS: return None
    try:
        r = requests.get(RAPIDAPI_BASE + path, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200: return r.json()
        print(f"  HTTP {r.status_code}: {path}")
    except Exception as e:
        print(f"  Error {path}: {e}")
    return None

# ── Parse scores from matchScore object ──────────────────────────────────────
def parse_scores(ms, t1_id):
    t1s = t2s = ""
    if not ms: return t1s, t2s
    inn = (ms.get("matchScoreDetails") or {}).get("inningsScoreList") or []
    for i in inn:
        s = f"{i.get('score',0)}/{i.get('wickets',0)} ({i.get('overs',0)}ov)"
        if str(i.get("batTeamId","")) == str(t1_id): t1s = s
        else: t2s = s
    if not t1s:
        t1sc = ms.get("team1Score",{}).get("inngs1",{})
        if isinstance(t1sc,dict) and t1sc.get("runs"):
            t1s = f"{t1sc['runs']}/{t1sc.get('wickets',0)} ({t1sc.get('overs',0)}ov)"
        t2sc = ms.get("team2Score",{}).get("inngs1",{})
        if isinstance(t2sc,dict) and t2sc.get("runs"):
            t2s = f"{t2sc['runs']}/{t2sc.get('wickets',0)} ({t2sc.get('overs',0)}ov)"
    return t1s, t2s

# ── Fetch scorecard from Cricbuzz ─────────────────────────────────────────────
def fetch_scorecard_cricbuzz(cricbuzz_id):
    data = api_get(f"/mcenter/v1/{cricbuzz_id}/hscard")
    if not data: return None
    scorecard = []
    for inn in data.get("scoreCard", []):
        bat  = (inn.get("batTeamDetails") or {}).get("batsmenData") or {}
        bowl = (inn.get("bowlTeamDetails") or {}).get("bowlersData") or {}
        batting = [{"batsman":b.get("batName",""),"dismissal":b.get("outDesc","not out"),
                    "r":b.get("runs",0),"b":b.get("balls",0),
                    "4s":b.get("fours",0),"6s":b.get("sixes",0),
                    "sr":round(b.get("strikeRate",0),1)} for b in bat.values() if b.get("batName")]
        bowling = [{"bowler":bw.get("bowlName",""),"o":bw.get("overs",0),
                    "m":bw.get("maidens",0),"r":bw.get("runs",0),
                    "w":bw.get("wickets",0),"econ":round(bw.get("economy",0),2)}
                   for bw in bowl.values() if bw.get("bowlName")]
        sd = inn.get("scoreDetails") or {}
        total = f"{sd.get('runs',0)}/{sd.get('wickets',0)} ({sd.get('overs',0)} ov)"
        tname = norm((inn.get("batTeamDetails") or {}).get("batTeamName",""))
        if batting:
            scorecard.append({"team":tname,"total":total,"batting":batting,"bowling":bowling})
    return scorecard or None

# ── Search Cricsheet raw files for a match ────────────────────────────────────
def search_cricsheet(t1, t2, date_str, fmt):
    fmt_map = {"T20I":"t20s","ODI":"odis","Test":"tests"}
    folder = fmt_map.get(fmt)
    if not folder: return None
    raw_path = os.path.join(RAW_DIR, f"{folder}_male_json")
    if not os.path.exists(raw_path): return None

    t1_low = t1.lower(); t2_low = t2.lower()
    year = date_str[:4] if date_str else ""
    
    # Search files — check recent ones first (sorted by name desc)
    files = sorted(glob.glob(os.path.join(raw_path, "*.json")), reverse=True)
    for fpath in files[:500]:  # check 500 most recent
        try:
            with open(fpath, encoding="utf-8") as f:
                m = json.load(f)
            info = m.get("info", {})
            teams = [t.lower() for t in info.get("teams", [])]
            dates = info.get("dates", [])
            if not dates: continue
            match_date = dates[0] if dates else ""
            if year and not match_date.startswith(year): continue
            if t1_low not in teams and t2_low not in teams: continue
            if not (t1_low in teams and t2_low in teams): continue
            if date_str and match_date != date_str: continue
            return build_scorecard_from_cricsheet(m, info)
        except Exception:
            continue
    return None

def build_scorecard_from_cricsheet(match_data, info):
    """Aggregate ball-by-ball Cricsheet data into batting/bowling summary."""
    innings_list = match_data.get("innings", [])
    scorecard = []
    
    for inn in innings_list:
        bat_team = inn.get("team", "")
        overs_data = inn.get("overs", [])
        
        # Aggregate batting
        batters = {}   # name → {r,b,4s,6s,dismissal}
        bat_order = []
        
        # Aggregate bowling  
        bowlers = {}   # name → {b,r,w,m,dots}
        
        legal_balls = {}  # bowler → legal ball count
        maiden_track = {}  # bowler → {over: [runs]}
        
        for over_obj in overs_data:
            over_n = over_obj.get("over", 0)
            for d in over_obj.get("deliveries", []):
                batter = d.get("batter", "")
                bowler = d.get("bowler", "")
                runs   = d.get("runs", {})
                bat_runs = runs.get("batter", 0)
                total_runs = runs.get("total", 0)
                extras = d.get("extras", {})
                is_wide = "wides" in extras
                is_nb   = "noballs" in extras
                
                # Batting
                if batter not in batters:
                    batters[batter] = {"r":0,"b":0,"4s":0,"6s":0,"dismissal":"not out"}
                    bat_order.append(batter)
                batters[batter]["r"] += bat_runs
                if not is_wide:
                    batters[batter]["b"] += 1
                if bat_runs == 4: batters[batter]["4s"] += 1
                if bat_runs == 6: batters[batter]["6s"] += 1
                
                # Wickets
                for wkt in d.get("wickets", []):
                    out_p = wkt.get("player_out","")
                    kind  = wkt.get("kind","")
                    fielders = wkt.get("fielders",[])
                    fnames = " & ".join(f.get("name","") for f in fielders if f.get("name"))
                    if kind in ("caught","c"):
                        dismissal = f"c {fnames} b {bowler}" if fnames else f"c & b {bowler}"
                    elif kind in ("bowled","b"):
                        dismissal = f"b {bowler}"
                    elif kind == "lbw":
                        dismissal = f"lbw b {bowler}"
                    elif kind in ("run out","run_out"):
                        dismissal = f"run out ({fnames})" if fnames else "run out"
                    elif kind == "stumped":
                        dismissal = f"st {fnames} b {bowler}" if fnames else f"st b {bowler}"
                    else:
                        dismissal = kind.replace("_"," ")
                    if out_p in batters:
                        batters[out_p]["dismissal"] = dismissal
                
                # Bowling
                if not is_wide and not is_nb:
                    if bowler not in legal_balls: legal_balls[bowler] = 0
                    legal_balls[bowler] += 1
                if bowler not in bowlers:
                    bowlers[bowler] = {"r":0,"w":0}
                    maiden_track[bowler] = {}
                bowlers[bowler]["r"] += total_runs
                for wkt in d.get("wickets", []):
                    if wkt.get("kind") not in ("run out","run_out","retired hurt","obstructing the field"):
                        bowlers[bowler]["w"] += 1
                # Track for maidens
                if not is_wide and not is_nb:
                    if over_n not in maiden_track[bowler]:
                        maiden_track[bowler][over_n] = 0
                    maiden_track[bowler][over_n] += total_runs

        # Calculate overs and maidens
        batting_rows = []
        for b in bat_order:
            s = batters[b]
            sr = round(s["r"]/s["b"]*100, 1) if s["b"] > 0 else 0
            batting_rows.append({"batsman":b,"dismissal":s["dismissal"],
                                  "r":s["r"],"b":s["b"],"4s":s["4s"],"6s":s["6s"],"sr":sr})
        
        bowling_rows = []
        for bw, stats in bowlers.items():
            balls = legal_balls.get(bw, 0)
            overs = balls // 6 + (balls % 6) / 10
            maidens = sum(1 for runs in maiden_track[bw].values() if runs == 0)
            econ = round(stats["r"] / (balls/6), 2) if balls >= 6 else 0
            bowling_rows.append({"bowler":bw,"o":round(overs,1),"m":maidens,
                                  "r":stats["r"],"w":stats["w"],"econ":econ})
        
        # Total from info
        total_str = ""
        target_info = inn.get("target", {})
        # Get total from last over
        if overs_data:
            last_over = overs_data[-1]
            total_runs_inn = sum(d.get("runs",{}).get("total",0) for ov in overs_data for d in ov.get("deliveries",[]))
            total_wkts = sum(len(d.get("wickets",[])) for ov in overs_data for d in ov.get("deliveries",[]))
            total_overs = len(overs_data)
            total_str = f"{total_runs_inn}/{total_wkts} ({total_overs} ov)"
        
        if batting_rows:
            scorecard.append({"team":norm(bat_team),"total":total_str,
                               "batting":batting_rows,"bowling":bowling_rows})
    
    return scorecard if scorecard else None

# ── Fetch matches from Cricbuzz ───────────────────────────────────────────────
def fetch_cricbuzz_matches():
    all_matches = []
    live_matches = []
    
    for category in ["live", "recent", "upcoming"]:
        data = api_get(f"/matches/v1/{category}")
        if not data: continue
        count = 0
        for typeMatch in data.get("typeMatches", []):
            if typeMatch.get("matchType","").lower() != "international":
                continue
            for sm in typeMatch.get("seriesMatches", []):
                wrapper = sm.get("seriesAdWrapper") or sm.get("series") or sm
                sname = (wrapper.get("seriesName") or wrapper.get("name") or "").lower()
                if any(w in sname for w in SKIP_SERIES): continue
                for m in (wrapper.get("matches") or []):
                    mi = m.get("matchInfo", {})
                    ms = m.get("matchScore", {})
                    t1_id = mi.get("team1",{}).get("teamId","")
                    t1 = norm(mi.get("team1",{}).get("teamName",""))
                    t2 = norm(mi.get("team2",{}).get("teamName",""))
                    fmt = mi.get("matchFormat","").upper()
                    if fmt == "T20": fmt = "T20I"
                    if fmt == "TEST": fmt = "Test"
                    t1s, t2s = parse_scores(ms, t1_id)
                    date_raw = mi.get("startDate","")
                    date_str = ms_to_date(date_raw) if str(date_raw).isdigit() else str(date_raw)[:10]
                    ended   = category == "recent"
                    started = category in ("recent","live")
                    series_display = (wrapper.get("seriesName") or wrapper.get("name") or f"cb-{mi.get('seriesId','')}")
                    entry = {
                        "id": f"cb-{mi.get('matchId','')}",
                        "name": f"{t1} vs {t2}, {mi.get('matchDesc','')}",
                        "matchType": fmt, "status": mi.get("status","Match not started"),
                        "venue": (mi.get("venueInfo") or {}).get("ground",""),
                        "date": date_str, "dateTimeGMT": date_str,
                        "t1":t1,"t2":t2,"t1s":t1s,"t2s":t2s,
                        "matchStarted":started,"matchEnded":ended,
                        "series_id": series_display,
                        "series": series_display,
                        "cricbuzz_id": mi.get("matchId",""),
                    }
                    if category == "live":
                        live_matches.append(entry)
                    all_matches.append(entry)
                    count += 1
        print(f"  {category}: {count} international matches")
    
    return live_matches, all_matches

# ── ICC calendar fallback schedule ───────────────────────────────────────────
ICC_SCHEDULE = [
    {"id":"nz-sa-t20-3","name":"New Zealand vs South Africa, 3rd T20I","matchType":"T20I","status":"Match not started","venue":"Saxton Oval, Nelson","date":"2026-03-21","t1":"New Zealand","t2":"South Africa","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"sa-nz-2026"},
    {"id":"eng-nz-test1-2026","name":"England vs New Zealand, 1st Test","matchType":"Test","status":"Match not started","venue":"Lord's Cricket Ground, London","date":"2026-06-04","t1":"England","t2":"New Zealand","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026"},
    {"id":"ind-afg-test-2026","name":"India vs Afghanistan, Only Test","matchType":"Test","status":"Match not started","venue":"M. Chinnaswamy Stadium, Bengaluru","date":"2026-06-06","t1":"India","t2":"Afghanistan","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026"},
    {"id":"ind-afg-odi1-2026","name":"India vs Afghanistan, 1st ODI","matchType":"ODI","status":"Match not started","venue":"Rajiv Gandhi Int. Stadium, Hyderabad","date":"2026-06-10","t1":"India","t2":"Afghanistan","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"afg-ind-2026"},
    {"id":"eng-nz-test2-2026","name":"England vs New Zealand, 2nd Test","matchType":"Test","status":"Match not started","venue":"Trent Bridge, Nottingham","date":"2026-06-12","t1":"England","t2":"New Zealand","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026"},
    {"id":"eng-nz-test3-2026","name":"England vs New Zealand, 3rd Test","matchType":"Test","status":"Match not started","venue":"Headingley, Leeds","date":"2026-06-25","t1":"England","t2":"New Zealand","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"nz-eng-2026"},
    {"id":"eng-ind-t20-1-2026","name":"England vs India, 1st T20I","matchType":"T20I","status":"Match not started","venue":"Edgbaston, Birmingham","date":"2026-07-01","t1":"England","t2":"India","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026"},
    {"id":"eng-ind-t20-2-2026","name":"England vs India, 2nd T20I","matchType":"T20I","status":"Match not started","venue":"Lord's Cricket Ground, London","date":"2026-07-04","t1":"England","t2":"India","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026"},
    {"id":"eng-ind-t20-3-2026","name":"England vs India, 3rd T20I","matchType":"T20I","status":"Match not started","venue":"The Oval, London","date":"2026-07-07","t1":"England","t2":"India","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026"},
    {"id":"eng-ind-odi-1-2026","name":"England vs India, 1st ODI","matchType":"ODI","status":"Match not started","venue":"Headingley, Leeds","date":"2026-07-17","t1":"England","t2":"India","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"ind-eng-2026"},
    {"id":"sa-aus-test1-2026","name":"South Africa vs Australia, 1st Test","matchType":"Test","status":"Match not started","venue":"Newlands, Cape Town","date":"2026-09-24","t1":"South Africa","t2":"Australia","t1s":"","t2s":"","matchStarted":False,"matchEnded":False,"series_id":"aus-sa-2026"},
]

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("="*55)
    print("  Cricklytics — Match Scraper")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

    all_matches = []
    live_matches = []

    if HAS_REQUESTS and RAPIDAPI_KEY != "YOUR_KEY":
        print("\n[1/3] Fetching from Cricbuzz RapidAPI...")
        live_matches, cb_matches = fetch_cricbuzz_matches()
        all_matches.extend(cb_matches)

        # Fetch scorecards for completed matches (senior teams only)
        SENIOR = {"India","Australia","England","Pakistan","South Africa","New Zealand",
                  "West Indies","Sri Lanka","Bangladesh","Afghanistan","Zimbabwe","Ireland"}
        print("\n[2/3] Fetching scorecards for completed matches...")
        for m in all_matches:
            if m.get("matchEnded") and not m.get("score"):
                if m.get("t1") in SENIOR or m.get("t2") in SENIOR:
                    cb_id = m.get("cricbuzz_id")
                    if cb_id:
                        sc = fetch_scorecard_cricbuzz(cb_id)
                        if sc:
                            m["score"] = sc
                            print(f"  Scorecard: {m['t1']} vs {m['t2']} ({m['date']})")
                        time.sleep(0.4)
    else:
        print("\n[1/3] Cricbuzz unavailable — using ICC calendar fallback")

    # Fill in ICC calendar for upcoming matches not in Cricbuzz
    cb_ids = {m["id"] for m in all_matches}
    for fixture in ICC_SCHEDULE:
        if fixture["id"] not in cb_ids:
            all_matches.append(fixture)

    # [3/3] Try Cricsheet for any completed matches without scorecard
    print("\n[3/3] Checking Cricsheet for missing scorecards...")
    cs_found = 0
    for m in all_matches:
        if m.get("matchEnded") and not m.get("score"):
            sc = search_cricsheet(m["t1"], m["t2"], m.get("date",""), m.get("matchType",""))
            if sc:
                m["score"] = sc
                cs_found += 1
                print(f"  Cricsheet: {m['t1']} vs {m['t2']} ({m['date']})")
    print(f"  Found {cs_found} scorecards in Cricsheet")

    # Preserve scorecards from existing matches.json
    existing_sc = {}
    existing_path = os.path.join(LIVE_DIR, "matches.json")
    if os.path.exists(existing_path):
        with open(existing_path, encoding="utf-8") as f:
            try:
                ex = json.load(f)
                for em in ex.get("data", []):
                    if em.get("score") and em["score"]:
                        existing_sc[em.get("id","")] = em["score"]
            except Exception:
                pass
    # Apply preserved scorecards to new matches
    for m in all_matches:
        if not m.get("score") and m.get("id") in existing_sc:
            m["score"] = existing_sc[m["id"]]



    # Sort: live → completed desc → upcoming asc
    def sort_key(m):
        live_flag = 1 if (m.get("matchStarted") and not m.get("matchEnded")) else 0
        comp_flag = 1 if m.get("matchEnded") else 0
        return (-live_flag, -comp_flag, m.get("date",""))
    all_matches.sort(key=sort_key)

    # Save
    with open(os.path.join(LIVE_DIR,"matches.json"),"w",encoding="utf-8") as f:
        json.dump({"data":all_matches,"source":"scraped","fetched_at":datetime.now(timezone.utc).isoformat()},f,indent=2,ensure_ascii=False)
    with open(os.path.join(LIVE_DIR,"live.json"),"w",encoding="utf-8") as f:
        json.dump({"data":live_matches,"source":"scraped","fetched_at":datetime.now(timezone.utc).isoformat()},f,indent=2,ensure_ascii=False)

    total = len(all_matches)
    comp  = sum(1 for m in all_matches if m.get("matchEnded"))
    upc   = sum(1 for m in all_matches if not m.get("matchStarted"))
    live  = len(live_matches)
    sc    = sum(1 for m in all_matches if m.get("score"))
    print(f"\n  ✓ matches.json — {total} total (Live:{live} Completed:{comp} Upcoming:{upc} Scorecards:{sc})")
    print(f"  ✓ live.json    — {live} live")
    print("="*55)
    print("  Done. Restart Flask.")
    print("="*55)

if __name__ == "__main__":
    main()
