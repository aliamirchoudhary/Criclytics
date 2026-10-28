"""
app.py
======
Cricklytics — Flask Backend
Serves pre-computed JSON files from data/processed/ and
live match data from CricAPI (Source A).

Usage:
    python app.py

Runs on: http://localhost:5000
"""

import json
import os
import re
import time
import requests
from collections import defaultdict
from datetime import datetime, timedelta

from pathlib import Path
from flask import current_app
from werkzeug.local import LocalProxy
from ..paths import PROJECT_ROOT
BASE_DIR = str(PROJECT_ROOT)
class ConfigPath(os.PathLike):
    def __init__(self, key):
        self.key = key
    def __fspath__(self):
        return os.fspath(current_app.config[self.key])

PROCESSED_DIR = ConfigPath("PROCESSED_DIR")
LIVE_DIR = ConfigPath("LIVE_DIR")
RAW_DIR = ConfigPath("RAW_DIR")
STATIC_DIR = ConfigPath("REFERENCE_DIR")

# Shared cache windows (minutes). All users within the window get cached data.
# This keeps upstream hits low while still refreshing often enough for UX.
LIVE_CACHE_TTL_MINUTES = 2
MATCH_INFO_CACHE_TTL_MINUTES = 10
SCORECARD_CACHE_TTL_MINUTES = 5
MATCH_LIST_CACHE_TTL_MINUTES = 15
SERIES_CACHE_TTL_MINUTES = 60

CRICAPI_KEY = LocalProxy(lambda: current_app.config["CRICAPI_KEY"])
CRICAPI_BASE = "https://api.cricapi.com/v1"
r_client = LocalProxy(lambda: current_app.extensions.get("redis"))
ml_engine = LocalProxy(lambda: current_app.extensions.get("probability_engine"))

def load_processed(filename):
    from .repository import safe_file
    repo = current_app.extensions['json_repository']
    data = repo.read(safe_file(PROCESSED_DIR, filename))
    return data if data is not None else repo.read(safe_file(BASE_DIR, filename))


def completed_match(match_id):
    from .repository import safe_file
    repo = current_app.extensions['json_repository']
    return (repo.match(safe_file(PROCESSED_DIR, 'completed_matches.json'), match_id)
            or repo.match(safe_file(BASE_DIR, 'completed_matches.json'), match_id))


def completed_summaries():
    from .repository import safe_file
    repo = current_app.extensions['json_repository']
    return (repo.summaries(safe_file(PROCESSED_DIR, 'completed_matches.json'))
            or repo.summaries(safe_file(BASE_DIR, 'completed_matches.json')))


def load_live(filename):
    return current_app.extensions['live_cache'].read(filename)


def resolve_match_detail(match_id):
        match_id = str(match_id or "").strip()
        if not match_id:
                return None

        match = completed_match(match_id)
        if match:
                return augment_completed_match(match)

        cached = load_live("matches.json")
        if cached:
                matches = cached.get("data") or cached.get("matches") or []
                for m in matches:
                        if str(m.get("id") or m.get("unique_id") or "") == match_id:
                                return m

        return None


def render_match_detail_bootstrap(match):
        if not isinstance(match, dict):
                return ""

        payload = json.dumps(match, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        return f"""
    <script>
        window.__CRICLYTICS_MATCH_DETAIL__ = {payload};
        (function() {{
            function escText(value) {{
                return String(value == null || value === '' ? '—' : value);
            }}

            function setText(selector, value) {{
                var el = document.querySelector(selector);
                if (el) el.textContent = escText(value);
            }}

            function setHtml(selector, value) {{
                var el = document.querySelector(selector);
                if (el) el.innerHTML = value || '';
            }}

            function render() {{
                var match = window.__CRICLYTICS_MATCH_DETAIL__;
                if (!match) return;
                var t1 = match.t1 || match.team1 || (Array.isArray(match.teams) ? match.teams[0] : '') || '';
                var t2 = match.t2 || match.team2 || (Array.isArray(match.teams) ? match.teams[1] : '') || '';
                var s1 = match.t1s || '';
                var s2 = match.t2s || '';

                if (!s1 || !s2) {{
                   var scoreArr = Array.isArray(match.score) ? match.score : [];
                   var t1s_found = false, t2s_found = false;

                   for (var i = 0; i < scoreArr.length; i++) {{
                       var sc = scoreArr[i];
                       var r = sc.r, w = sc.w, o = sc.o, inn = String(sc.inning || "").toLowerCase();
                       var scoreStr = [r, w != null ? '/' + w : '', o != null ? ' (' + o + 'o)' : ''].join('');

                       if (inn.includes(t1.toLowerCase())) {{ s1 = scoreStr; t1s_found = true; }}
                       else if (inn.includes(t2.toLowerCase())) {{ s2 = scoreStr; t2s_found = true; }}
                   }}

                   // Positional fallback only if name match failed AND not belonging to other
                   if (!s1 && scoreArr[0] && !t2s_found) s1 = [scoreArr[0].r, scoreArr[0].w != null ? '/' + scoreArr[0].w : '', scoreArr[0].o != null ? ' (' + scoreArr[0].o + 'o)' : ''].join('');
                   if (!s2 && scoreArr[1]) s2 = [scoreArr[1].r, scoreArr[1].w != null ? '/' + scoreArr[1].w : '', scoreArr[1].o != null ? ' (' + scoreArr[1].o + 'o)' : ''].join('');
                }}

                setText('#team1Name', t1);
                setText('#team2Name', t2);
                setText('#team1Score', s1 || '—');
                setText('#team2Score', s2 || '—');

                var status = match.matchEnded ? (match.status || 'Completed') : (match.matchStarted ? (match.status || 'Live') : (match.status || 'Upcoming'));
                var statusEl = document.querySelector('.match-status-live');
                if (statusEl) statusEl.textContent = status;

                setText('#matchVenue', match.venue || '');
                setText('#matchSeries', match.series || '');
                setText('#matchDate', match.date || '');

                var infoRows = document.querySelectorAll('.info-row');
                infoRows.forEach(function(row) {{
                    var label = ((row.querySelector('.info-row-label') || {{}}).textContent || '').trim();
                    var valueEl = row.querySelector('.info-row-value');
                    if (!valueEl) return;
                    if (label === 'Series') valueEl.textContent = match.series || '—';
                    else if (label === 'Match') valueEl.textContent = match.name || '—';
                    else if (label === 'Venue') valueEl.textContent = match.venue || '—';
                    else if (label === 'Date & Time') valueEl.textContent = match.date || match.dateTimeGMT || '—';
                    else if (label === 'Toss') valueEl.textContent = match.toss || '—';
                    else if (label === 'Squads') valueEl.textContent = Array.isArray(match.teams) ? match.teams.join(' · ') : '—';
                    else if (label === 'Umpires') valueEl.textContent = match.umpires ? match.umpires.join(' · ') : '—';
                    else if (label === 'Match Referee') valueEl.textContent = match.match_referee || '—';
                    else if (label === 'Series Score') valueEl.textContent = match.status || '—';
                }});

                if (typeof window.updateScoreboard === 'function') window.updateScoreboard(match);
                if (typeof window.updateCricsheetSections === 'function') window.updateCricsheetSections(match, t1, t2);
                if (typeof window.updateBattingScorecard === 'function' && Array.isArray(match.innings)) {{
                    if (match.innings && match.innings.length > 0 && Array.isArray(match.innings[0].batting)) window.updateBattingScorecard(match.innings[0].batting, 'innings1-batting');
                    if (match.innings && match.innings.length > 0 && Array.isArray(match.innings[0].bowling)) window.updateBowlingScorecard(match.innings[0].bowling, 'innings1-bowling');
                    if (match.innings && match.innings.length > 1 && Array.isArray(match.innings[1].batting)) window.updateBattingScorecard(match.innings[1].batting, 'innings2-batting');
                    if (match.innings && match.innings.length > 1 && Array.isArray(match.innings[1].bowling)) window.updateBowlingScorecard(match.innings[1].bowling, 'innings2-bowling');
                }}
                if (typeof window.populateKeyPlayers === 'function') window.populateKeyPlayers(match);
                if (typeof window.updateWinProbability === 'function') window.updateWinProbability(match, t1, t2);
                if (typeof window.updateH2H === 'function' && t1 && t2) window.updateH2H(t1, t2);
                if (typeof window.updateVenueContext === 'function' && match.venue) window.updateVenueContext(match.venue);

                // COMPLETED: hide live-only sections for completed matches
                if (match.matchEnded) {{
                    document.querySelectorAll('.section-card').forEach(function(card) {{
                        var t = ((card.querySelector('.section-card-title') || {{}}).textContent || '');
                        if (t.includes('Live Snapshot') || t.includes('At the Crease') || t.includes('Current Bowlers') || t.includes('Recent Deliveries')) {{
                            card.style.display = 'none';
                        }}
                    }});
                    var winProbCard = document.getElementById('win-prob-card');
                    if (winProbCard) {{
                        winProbCard.style.display = 'none';
                        winProbCard.style.visibility = 'hidden';
                    }}
                    document.querySelectorAll('.target-box').forEach(function(el) {{ el.classList.add('hide-for-completed'); el.style.display='none'; }});
                    document.querySelectorAll('.run-rate-box').forEach(function(el) {{ el.classList.add('hide-for-completed'); el.style.display='none'; }});
                    document.querySelectorAll('.chase-bar-wrap').forEach(function(el) {{ el.classList.add('hide-for-completed'); el.style.display='none'; }});
                }}
            }}

            if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
            else render();
        }})();
    </script>
"""


RAW_MATCH_DIRS = LocalProxy(lambda: [
    os.path.join(RAW_DIR, "tests_male_json"),
    os.path.join(RAW_DIR, "odis_male_json"),
    os.path.join(RAW_DIR, "t20s_male_json"),
])


def load_raw_cricsheet_match(match_id):
    from .repository import safe_file
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', str(match_id or '')):
        return None
    for folder in RAW_MATCH_DIRS:
        data = current_app.extensions['json_repository'].read(safe_file(folder, str(match_id) + '.json'))
        if data:
            return data
    return None


def format_cricsheet_toss(toss):
    if not isinstance(toss, dict):
        return ""
    winner = str(toss.get("winner") or "").strip()
    decision = str(toss.get("decision") or "").strip().lower()
    if winner and decision:
        if decision == "bat":
            decision = "bat"
        elif decision == "field":
            decision = "bowl"
        return f"{winner} won the toss and chose to {decision}"
    return winner or str(toss.get("decision") or "").strip()


def format_cricsheet_officials(officials):
    officials = officials if isinstance(officials, dict) else {}
    return {
        "match_referees": officials.get("match_referees") or [],
        "umpires": officials.get("umpires") or [],
        "tv_umpires": officials.get("tv_umpires") or [],
        "reserve_umpires": officials.get("reserve_umpires") or [],
    }


def summarize_match_score(match):
    scores = (match or {}).get("score") or []
    parts = []
    for score in scores:
        if not isinstance(score, dict):
            continue
        runs = score.get("r")
        wickets = score.get("w")
        overs = score.get("o")
        if runs is None:
            continue
        part = f"{runs}/{wickets if wickets is not None else '—'}"
        if overs is not None:
            part += f" ({overs}o)"
        inning_team = str(score.get("inning") or score.get("team") or "").split(" Inning")[0].strip()
        if inning_team:
            part = f"{inning_team} {part}"
        parts.append(part)
    return " · ".join(parts)


def format_overs_from_balls(balls):
    balls = int(balls or 0)
    return f"{balls // 6}.{balls % 6}"


def format_dismissal_text(kind, batter, bowler, fielders=None):
    kind = str(kind or "").strip().lower()
    bowler = str(bowler or "").strip()
    batter = str(batter or "").strip()
    fielders = fielders or []
    fielder = str(fielders[0] if fielders else "").strip()

    if kind == "caught":
        return f"c {fielder} b {bowler}" if fielder else f"c b {bowler}"
    if kind == "bowled":
        return f"b {bowler}"
    if kind in ("lbw", "hit wicket"):
        return f"{kind} b {bowler}"
    if kind == "stumped":
        return f"st {fielder} b {bowler}" if fielder else f"st b {bowler}"
    if kind == "run out":
        return f"run out ({fielder})" if fielder else "run out"
    if kind:
        return kind
    return "not out"


def build_cricsheet_match_view(raw_match):
    info = raw_match.get("info") or {}
    innings_views = []
    all_partnerships = []
    top_scorer = None
    best_bowler = None

    for inning_index, inning in enumerate(raw_match.get("innings") or []):
        batting_team = inning.get("team") or ""
        bowling_team = next((team for team in (info.get("teams") or []) if team != batting_team), "")
        batting_map = {}
        bowling_map = {}
        over_tracker = defaultdict(lambda: {"runs": 0, "balls": 0})
        innings_runs = 0
        wickets = 0
        legal_balls = 0
        boundaries = 0
        dot_balls = 0
        partnership_runs = 0
        fall_of_wickets = []
        order = 0

        for over in inning.get("overs", []):
            over_num = over.get("over", 0)
            for delivery_index, delivery in enumerate(over.get("deliveries", []), start=1):
                batter = str(delivery.get("batter") or "").strip()
                bowler = str(delivery.get("bowler") or "").strip()
                non_striker = str(delivery.get("non_striker") or "").strip()
                runs = delivery.get("runs") or {}
                extras = delivery.get("extras") or {}
                wickets_info = delivery.get("wickets") or []

                batter_runs = int(runs.get("batter") or 0)
                total_runs = int(runs.get("total") or 0)
                wides = int(extras.get("wides") or 0)
                noballs = int(extras.get("noballs") or 0)
                byes = int(extras.get("byes") or 0)
                legbyes = int(extras.get("legbyes") or 0)
                legal_ball = wides == 0 and noballs == 0

                if batter and batter not in batting_map:
                    order += 1
                    batting_map[batter] = {
                        "batsman": batter,
                        "dismissal": "not out",
                        "r": 0,
                        "b": 0,
                        "4s": 0,
                        "6s": 0,
                        "sr": 0,
                        "order": order,
                    }

                if bowler and bowler not in bowling_map:
                    bowling_map[bowler] = {
                        "bowler": bowler,
                        "o": 0,
                        "m": 0,
                        "r": 0,
                        "w": 0,
                        "eco": 0,
                        "wd": 0,
                        "nb": 0,
                    }

                innings_runs += total_runs
                partnership_runs += total_runs
                if legal_ball:
                    legal_balls += 1

                if legal_ball and total_runs == 0:
                    dot_balls += 1
                if batter_runs in (4, 6):
                    boundaries += 1

                if batter and batter in batting_map:
                    batting_map[batter]["r"] += batter_runs
                    if legal_ball:
                        batting_map[batter]["b"] += 1
                    if batter_runs == 4:
                        batting_map[batter]["4s"] += 1
                    if batter_runs == 6:
                        batting_map[batter]["6s"] += 1

                if bowler and bowler in bowling_map:
                    bowler_runs = batter_runs + wides + noballs
                    bowling_map[bowler]["r"] += bowler_runs
                    if legal_ball:
                        bowling_map[bowler]["o"] += 1
                    bowling_map[bowler]["wd"] += wides
                    bowling_map[bowler]["nb"] += noballs
                    over_tracker[(bowler, over_num)]["runs"] += bowler_runs
                    if legal_ball:
                        over_tracker[(bowler, over_num)]["balls"] += 1

                if wickets_info:
                    wicket = wickets_info[0] or {}
                    kind = wicket.get("kind") or ""
                    player_out = str(wicket.get("player_out") or batter or "").strip()
                    fielders = [f.get("name") for f in wicket.get("fielders") or [] if f.get("name")]
                    wickets += 1
                    dismissal = format_dismissal_text(kind, player_out, bowler, fielders)
                    if player_out in batting_map:
                        batting_map[player_out]["dismissal"] = dismissal

                    if bowler and bowler in bowling_map and kind.lower() not in ("run out", "retired hurt", "retired out"):
                        bowling_map[bowler]["w"] += 1

                    fall_of_wickets.append(
                        f"{innings_runs}/{wickets} ({player_out}, {format_overs_from_balls(legal_balls)} ov)"
                    )
                    all_partnerships.append({
                        "innings": inning_index + 1,
                        "team": batting_team,
                        "wicket_no": wickets,
                        "label": f"{wickets}{'st' if wickets == 1 else 'nd' if wickets == 2 else 'rd' if wickets == 3 else 'th'} wicket",
                        "names": " & ".join([n for n in [batter, non_striker] if n]),
                        "runs": partnership_runs,
                        "score": innings_runs,
                    })
                    partnership_runs = 0

        batting_rows = list(batting_map.values())
        bowling_rows = list(bowling_map.values())

        for row in batting_rows:
            balls = int(row["b"] or 0)
            row["sr"] = round((row["r"] * 100.0 / balls), 1) if balls else 0

        for row in bowling_rows:
            balls = int(row["o"] or 0)
            row["m"] = sum(
                1
                for (bowler_name, over_num), stats in over_tracker.items()
                if bowler_name == row["bowler"] and stats["balls"] == 6 and stats["runs"] == 0
            )
            row["o"] = format_overs_from_balls(balls)
            row["eco"] = round((row["r"] * 6.0 / balls), 1) if balls else 0

        batting_rows.sort(key=lambda row: row.get("order", 999))
        bowling_rows.sort(key=lambda row: (-row.get("w", 0), row.get("r", 0), row.get("bowler", "")))

        innings_view = {
            "team": batting_team,
            "batting": batting_rows,
            "bowling": bowling_rows,
            "fall_of_wickets": fall_of_wickets,
            "partnerships": [],
            "total": innings_runs,
            "wickets": wickets,
            "overs": format_overs_from_balls(legal_balls),
            "boundaries": boundaries,
            "dot_balls": dot_balls,
        }

        if batting_rows:
            innings_view["top_scorer"] = max(batting_rows, key=lambda row: (row.get("r", 0), -row.get("b", 0)))
        if bowling_rows:
            innings_view["best_bowler"] = max(
                bowling_rows,
                key=lambda row: (row.get("w", 0), -row.get("r", 0), row.get("m", 0)),
            )

        innings_views.append(innings_view)

        if innings_view.get("top_scorer"):
            scorer = innings_view["top_scorer"]
            candidate = {
                "name": scorer.get("batsman", ""),
                "runs": scorer.get("r", 0),
                "team": batting_team,
            }
            if not top_scorer or candidate["runs"] > top_scorer["runs"]:
                top_scorer = candidate

        if innings_view.get("best_bowler"):
            bowler = innings_view["best_bowler"]
            candidate = {
                "name": bowler.get("bowler", ""),
                "wickets": bowler.get("w", 0),
                "runs": bowler.get("r", 0),
                "overs": bowler.get("o", "0.0"),
                "team": bowling_team,
            }
            if not best_bowler or (candidate["wickets"], -candidate["runs"]) > (best_bowler["wickets"], -best_bowler["runs"]):
                best_bowler = candidate

    partnerships = sorted(all_partnerships, key=lambda item: (-item.get("runs", 0), item.get("innings", 99), item.get("wicket_no", 99)))[:5]

    return {
        "innings": innings_views,
        "partnerships": partnerships,
        "match_stats": {
            "innings": [
                {
                    "team": inning.get("team", ""),
                    "boundaries": inning.get("boundaries", 0),
                    "dot_balls": inning.get("dot_balls", 0),
                    "top_scorer": inning.get("top_scorer", {}),
                    "best_bowler": inning.get("best_bowler", {}),
                }
                for inning in innings_views[:2]
            ],
            "top_scorer": top_scorer or {},
            "best_bowler": best_bowler or {},
        },
    }


def augment_completed_match(match):
    if not isinstance(match, dict):
        return match

    # If the match is already "Mega-Enriched" (from our updated processing script),
    # we don't need to load the raw file at all.
    if "innings" in match and match.get("innings"):
        # We still need to ensure basic fields like scoreText and result are set
        match["scoreText"] = match.get("scoreText") or summarize_match_score(match)

        # Prediction check for Context Insights
        if ml_engine:
            try:
                t1, t2 = match.get("team1"), match.get("team2")
                fmt = match.get("format", "T20")
                if t1 and t2:
                    pred = ml_engine.team_match_outcome(t1, t2, format=fmt)
                    match["prediction"] = pred
                    if pred and "team_a" in pred:
                        match["team_a_prob"] = pred["team_a"].get("win_probability", 0.5)
                        match["team_b_prob"] = pred["team_b"].get("win_probability", 0.5)
            except: pass
        return match

    match_id = str(match.get("id") or match.get("unique_id") or "").strip()
    raw_match = load_raw_cricsheet_match(match_id)
    if not raw_match:
        return match

    info = raw_match.get("info") or {}
    officials = format_cricsheet_officials(info.get("officials") or {})
    toss = info.get("toss") or {}
    players = info.get("players") or {}
    enriched = dict(match)

    if not enriched.get("city"):
        enriched["city"] = info.get("city") or ""
    if not enriched.get("venue"):
        enriched["venue"] = info.get("venue") or enriched.get("venue") or ""
    if not enriched.get("series"):
        enriched["series"] = (info.get("event") or {}).get("name") or enriched.get("series") or ""
    if not enriched.get("date"):
        dates = info.get("dates") or []
        if dates:
            enriched["date"] = dates[0]
            enriched["dateTimeGMT"] = dates[0]

    enriched["toss"] = enriched.get("toss") or format_cricsheet_toss(toss)
    enriched["toss_details"] = toss
    enriched["officials"] = officials
    enriched["match_referee"] = (officials.get("match_referees") or [""])[0] or enriched.get("match_referee") or ""
    enriched["umpires"] = officials.get("umpires") or []
    enriched["tv_umpires"] = officials.get("tv_umpires") or []
    enriched["reserve_umpires"] = officials.get("reserve_umpires") or []
    enriched["players"] = players
    enriched["squads"] = players

    cricsheet_view = build_cricsheet_match_view(raw_match)
    enriched["innings"] = cricsheet_view.get("innings") or enriched.get("innings") or []
    enriched["partnerships"] = cricsheet_view.get("partnerships") or []
    enriched["match_stats"] = cricsheet_view.get("match_stats") or {}

    if not enriched.get("player_of_match"):
        enriched["player_of_match"] = info.get("player_of_match") or []

    enriched["balls_per_over"] = info.get("balls_per_over")
    enriched["season"] = info.get("season")
    enriched["match_type_number"] = info.get("match_type_number")
    enriched["team_type"] = info.get("team_type")
    enriched["scoreText"] = enriched.get("scoreText") or summarize_match_score(enriched)

    if not enriched.get("score"):
        enriched["score"] = [
            {
                "team": inning.get("team", ""),
                "r": inning.get("total", 0),
                "w": inning.get("wickets", 0),
                "o": inning.get("overs", "0.0"),
            }
            for inning in cricsheet_view.get("innings") or []
        ]

    return enriched

def save_live(filename, data, ttl_minutes=60):
    return current_app.extensions['live_cache'].write(filename, data, ttl_minutes)


def normalize_name(name):
    return re.sub(r'[^a-z0-9]+', '', name.lower()) if name else ''


def is_cricapi_failure_payload(data):
    return isinstance(data, dict) and str(data.get('status', '')).lower() == 'failure'


def cache_age_minutes(filename):
    return current_app.extensions['live_cache'].age(filename)


def fetch_cricapi(endpoint, params=None, cache_file=None, max_age_minutes=60):
    cache = current_app.extensions['live_cache']
    cached = cache.read(cache_file) if cache_file else None
    if cached and cache.age(cache_file) < max_age_minutes:
        return cached
    if not current_app.config['LIVE_FETCH_ENABLED'] or not CRICAPI_KEY:
        return cached
    if endpoint not in {'matches', 'currentMatches', 'match_info', 'match_scorecard', 'series'}:
        return cached
    # Unknown public IDs cannot allocate files or consume provider calls.
    if params and params.get('id'):
        known = cache.read('matches.json') or {}
        rows = known.get('data') or known.get('matches') or []
        if not any(str(m.get('id') or m.get('unique_id')) == str(params['id']) for m in rows):
            return cached
    try:
        owner = cache.acquire()
    except Exception:
        return cached
    if not owner:
        return cached
    backoff = 2
    try:
        if cache_file and cache.age(cache_file) < max_age_minutes:
            return cache.read(cache_file)
        arguments = dict(params or {})
        arguments['apikey'] = str(CRICAPI_KEY)
        response = requests.get(f'{CRICAPI_BASE}/{endpoint}', params=arguments, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or is_cricapi_failure_payload(data):
            backoff = 15 * 60
            return cached
        if cache_file:
            cache.write(cache_file, data, max_age_minutes)
        return data
    except Exception as error:
        backoff = 60
        current_app.logger.warning('Provider refresh failed type=%s', type(error).__name__)
        return cached
    finally:
        cache.release(owner, backoff)
