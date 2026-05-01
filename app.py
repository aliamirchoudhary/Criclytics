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
import threading
import requests
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from flask import Flask, jsonify, request, send_from_directory, abort, make_response
from dotenv import load_dotenv
from flask_cors import CORS
import redis
from ml_probability_engine import ProbabilityEngine

load_dotenv()

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)  # Enable CORS for cross-domain frontend access

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
LIVE_DIR      = os.path.join(BASE_DIR, "data", "live")
RAW_DIR       = os.path.join(BASE_DIR, "data", "raw")
STATIC_DIR = os.path.join(BASE_DIR, "data", "static")
os.makedirs(LIVE_DIR, exist_ok=True)

# Simple in-process backoff when CricAPI reports quota blocking.
CRICAPI_BLOCK_UNTIL = 0
CRICAPI_BLOCK_REASON = ""

# Shared cache windows (minutes). All users within the window get cached data.
# This keeps upstream hits low while still refreshing often enough for UX.
LIVE_CACHE_TTL_MINUTES = 2
MATCH_INFO_CACHE_TTL_MINUTES = 10
SCORECARD_CACHE_TTL_MINUTES = 5
MATCH_LIST_CACHE_TTL_MINUTES = 15
SERIES_CACHE_TTL_MINUTES = 60

# Prevent expiry stampede: only one thread refreshes each cache file at a time.
_CACHE_LOCKS_GUARD = threading.Lock()
_CACHE_LOCKS = {}

# ── CricAPI config ────────────────────────────────────────────────────────────
# Replace with your actual key from cricapi.com
CRICAPI_KEY  = os.environ.get("CRICAPI_KEY", "")
CRICAPI_BASE = "https://api.cricapi.com/v1"

# ── Redis (Upstash) setup ─────────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "")
r_client = None
if REDIS_URL:
    try:
        # upstash uses rediss:// for TLS
        r_client = redis.from_url(REDIS_URL, decode_responses=True)
        print("[Redis] Connected successfully")
    except Exception as e:
        print(f"[Redis] Connection failed: {e}")

# ── Redis (Upstash) setup ─────────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "")
r_client = None
if REDIS_URL:
    try:
        # upstash uses rediss:// for TLS
        r_client = redis.from_url(REDIS_URL, decode_responses=True)
        print("[Redis] Connected successfully")
    except Exception as e:
        print(f"[Redis] Connection failed: {e}")

# ── ML Probability Engine ─────────────────────────────────────────────────────
# Initialize the ML probability engine for predictions
ml_engine = None
try:
    ml_engine = ProbabilityEngine(data_dir=PROCESSED_DIR)
    print("[ML Engine] Initialized successfully")
except Exception as e:
    print(f"[ML Engine] Failed to initialize: {e}")

# ── Helper: load a processed JSON file ───────────────────────────────────────
def load_processed(filename):
    # Try expected subdirectory
    path = os.path.join(PROCESSED_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    
    # Smart Fallback: Try root directory (Hugging Face style)
    root_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(root_path):
        with open(root_path, encoding="utf-8") as f:
            return json.load(f)
            
    return None

# ── Helper: load a live cache file ───────────────────────────────────────────
def load_live(filename):
    if r_client:
        try:
            data = r_client.get(filename)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"[Redis] Load error ({filename}): {e}")
            
    # Try expected subdirectory
    path = os.path.join(LIVE_DIR, filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
            
    # Smart Fallback: Try root directory
    root_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(root_path):
        with open(root_path, encoding="utf-8") as f:
            return json.load(f)
            
    return None


def resolve_match_detail(match_id):
        match_id = str(match_id or "").strip()
        if not match_id:
                return None

        completed_data = load_processed("completed_matches.json")
        if completed_data:
                completed = completed_data.get("data") or []
                for m in completed:
                        if str(m.get("id") or m.get("unique_id") or "") == match_id:
                                return augment_completed_match(m)

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

        payload = json.dumps(match, ensure_ascii=False)
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
                var score = Array.isArray(match.score) ? match.score : [];
                var s1 = match.t1s || (score[0] ? [score[0].r, score[0].w != null ? '/' + score[0].w : '', score[0].o != null ? ' (' + score[0].o + 'o)' : ''].join('') : '—');
                var s2 = match.t2s || (score[1] ? [score[1].r, score[1].w != null ? '/' + score[1].w : '', score[1].o != null ? ' (' + score[1].o + 'o)' : ''].join('') : '—');

                setText('#team1Name', t1);
                setText('#team2Name', t2);
                setText('#team1Score', s1);
                setText('#team2Score', s2);

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


RAW_MATCH_DIRS = [
    os.path.join(RAW_DIR, "tests_male_json"),
    os.path.join(RAW_DIR, "odis_male_json"),
    os.path.join(RAW_DIR, "t20s_male_json"),
]


@lru_cache(maxsize=512)
def load_raw_cricsheet_match(match_id):
    match_id = str(match_id or "").strip()
    if not match_id:
        return None

    for folder in RAW_MATCH_DIRS:
        path = os.path.join(folder, f"{match_id}.json")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
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
    if r_client:
        try:
            r_client.set(filename, json.dumps(data, ensure_ascii=False), ex=int(ttl_minutes * 60))
            return
        except Exception as e:
            print(f"[Redis] Save error ({filename}): {e}")

    path = os.path.join(LIVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def is_cricapi_failure_payload(data):
    return isinstance(data, dict) and str(data.get("status", "")).lower() == "failure"

def cache_age_minutes(filename):
    """Returns how many minutes ago a live cache file was written."""
    if r_client:
        try:
            ttl = r_client.ttl(filename)
            if ttl < 0: return 9999
            # Approximate age based on common TTLs (60 mins default)
            # This is only used for relative comparison in fetch_cricapi
            return 0 # If it exists in Redis, we treat it as fresh in the check below
        except Exception:
            pass

    path = os.path.join(LIVE_DIR, filename)
    if not os.path.exists(path):
        return 9999
    age = time.time() - os.path.getmtime(path)
    return age / 60


def _get_cache_lock(cache_file):
    if not cache_file:
        return None
    with _CACHE_LOCKS_GUARD:
        if cache_file not in _CACHE_LOCKS:
            _CACHE_LOCKS[cache_file] = threading.Lock()
        return _CACHE_LOCKS[cache_file]

# ── CricAPI fetch with caching ────────────────────────────────────────────────
def fetch_cricapi(endpoint, params=None, cache_file=None, max_age_minutes=60):
    """
    Fetch from CricAPI. Serves from cache if fresh enough.
    max_age_minutes: how old the cache can be before re-fetching.
    """
    global CRICAPI_BLOCK_UNTIL, CRICAPI_BLOCK_REASON

    def get_fresh_cache():
        if not cache_file:
            return None
        if cache_age_minutes(cache_file) < max_age_minutes:
            cached = load_live(cache_file)
            if cached and not is_cricapi_failure_payload(cached):
                return cached
        return None

    fresh = get_fresh_cache()
    if fresh is not None:
        return fresh

    cache_lock = _get_cache_lock(cache_file)
    if cache_lock is not None:
        # Wait for any in-flight refresh for this cache key, then re-check cache.
        if cache_lock.acquire(timeout=15):
            try:
                fresh = get_fresh_cache()
                if fresh is not None:
                    return fresh

                if time.time() < CRICAPI_BLOCK_UNTIL:
                    cached = load_live(cache_file)
                    if cached and not is_cricapi_failure_payload(cached):
                        return cached
                    return {"status": "failure", "reason": CRICAPI_BLOCK_REASON or "Temporarily blocked"}

                if CRICAPI_KEY == "YOUR_CRICAPI_KEY_HERE":
                    return None

                try:
                    p = {"apikey": CRICAPI_KEY}
                    if params:
                        p.update(params)
                    resp = requests.get(f"{CRICAPI_BASE}/{endpoint}", params=p, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()

                    if is_cricapi_failure_payload(data):
                        reason = str(data.get("reason") or "")
                        reason_l = reason.lower()
                        if "block" in reason_l or ("hits" in reason_l and "exceed" in reason_l):
                            CRICAPI_BLOCK_UNTIL = time.time() + (15 * 60)
                            CRICAPI_BLOCK_REASON = reason or "Blocked for 15 minutes"

                        cached = load_live(cache_file)
                        if cached and not is_cricapi_failure_payload(cached):
                            return cached
                        return data

                    save_live(cache_file, data, ttl_minutes=max_age_minutes)
                    return data
                except Exception as e:
                    print(f"  CricAPI error ({endpoint}): {e}")
                    return load_live(cache_file)
            finally:
                cache_lock.release()

        # Could not acquire lock quickly; another request is refreshing now.
        cached = load_live(cache_file)
        if cached and not is_cricapi_failure_payload(cached):
            return cached
        return {"status": "failure", "reason": "Refresh in progress"}

    if time.time() < CRICAPI_BLOCK_UNTIL:
        # During provider block windows, do not hit the API repeatedly.
        if cache_file:
            cached = load_live(cache_file)
            if cached and not is_cricapi_failure_payload(cached):
                return cached
        return {"status": "failure", "reason": CRICAPI_BLOCK_REASON or "Temporarily blocked"}

    if CRICAPI_KEY == "YOUR_CRICAPI_KEY_HERE":
        # No key set — return empty so frontend falls back to dummy data
        return None

    try:
        p = {"apikey": CRICAPI_KEY}
        if params:
            p.update(params)
        resp = requests.get(f"{CRICAPI_BASE}/{endpoint}", params=p, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if is_cricapi_failure_payload(data):
            reason = str(data.get("reason") or "")
            reason_l = reason.lower()
            if "block" in reason_l or ("hits" in reason_l and "exceed" in reason_l):
                CRICAPI_BLOCK_UNTIL = time.time() + (15 * 60)
                CRICAPI_BLOCK_REASON = reason or "Blocked for 15 minutes"

            # Never overwrite good cache with provider failure payloads.
            if cache_file:
                cached = load_live(cache_file)
                if cached and not is_cricapi_failure_payload(cached):
                    return cached
            return data

        if cache_file:
            save_live(cache_file, data, ttl_minutes=max_age_minutes)
        return data
    except Exception as e:
        print(f"  CricAPI error ({endpoint}): {e}")
        # Return stale cache if available
        if cache_file:
            return load_live(cache_file)
        return None


# ════════════════════════════════════════════════════════════════════════════
# STATIC FILE SERVING — serve your HTML pages
# ════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    response = make_response(send_from_directory(BASE_DIR, "index.html"))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/match-detail.html")
def match_detail_page():
    path = os.path.join(BASE_DIR, "match-detail.html")
    with open(path, encoding="utf-8") as f:
        html = f.read()

    match_id = request.args.get("id", "").strip()
    match = resolve_match_detail(match_id) if match_id else None
    if match:
        bootstrap = render_match_detail_bootstrap(match)
        if "</body>" in html:
            html = html.replace("</body>", bootstrap + "\n</body>")
        else:
            html = html.replace("</html>", bootstrap + "\n</html>")

    response = make_response(html)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/<path:filename>")
def static_files(filename):
    """Serve any HTML, CSS, JS, or image file from the project root."""
    if filename.lower() == "match-detail.html":
        path = os.path.join(BASE_DIR, "match-detail.html")
        with open(path, encoding="utf-8") as f:
            html = f.read()

        match_id = request.args.get("id", "").strip()
        match = resolve_match_detail(match_id) if match_id else None
        if match:
            bootstrap = render_match_detail_bootstrap(match)
            if "</body>" in html:
                html = html.replace("</body>", bootstrap + "\n</body>")
            else:
                html = html.replace("</html>", bootstrap + "\n</html>")

        response = make_response(html)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    response = make_response(send_from_directory(BASE_DIR, filename))
    if filename.lower().endswith((".html", ".js", ".css")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ════════════════════════════════════════════════════════════════════════════
# SOURCE B ENDPOINTS — serve pre-computed Cricsheet data
# ════════════════════════════════════════════════════════════════════════════

# ── Players ──────────────────────────────────────────────────────────────────

@app.route("/api/players")
def get_players():
    """
    All players with career stats.
    Query params:
        format    — filter by format: Test / ODI / T20I
        country   — filter by country name (partial match)
        role      — bat / bowl / all (default: all)
        search    — search by name (partial match)
        sort      — runs / wickets / avg / sr (default: runs)
        limit     — number of results (default: 50)
        offset    — pagination offset (default: 0)
    """
    data = load_processed("players_index.json")
    if data is None:
        return jsonify({"error": "players_index.json not found — run process_cricsheet.py first"}), 500

    fmt     = request.args.get("format")
    country = request.args.get("country", "").lower()
    role    = request.args.get("role", "all").lower()
    search  = request.args.get("search", "").lower()
    sort    = request.args.get("sort", "runs")
    limit   = int(request.args.get("limit", 50))
    offset  = int(request.args.get("offset", 0))

    players = list(data.values())

    # Filter by format
    if fmt:
        players = [p for p in players if fmt in p.get("formats", [])]

    # Filter by name search
    if search:
        players = [p for p in players if search in p["name"].lower()]

    # Filter by country (now stored directly on player from Cricsheet)
    if country:
        players = [p for p in players if country in (p.get("country","") or "").lower()]

    # Filter by role
    if role == "bat":
        players = [p for p in players if p.get("batting")]
    elif role == "bowl":
        players = [p for p in players if p.get("bowling")]

    # Sort
    def sort_key(p):
        if sort == "wickets":
            total = sum(f.get("wickets", 0) for f in p.get("bowling", {}).values())
            return total
        elif sort == "avg":
            avgs = [f.get("average", 0) for f in p.get("batting", {}).values()]
            return max(avgs) if avgs else 0
        elif sort == "sr":
            srs = [f.get("strike_rate", 0) for f in p.get("batting", {}).values()]
            return max(srs) if srs else 0
        else:  # runs (default)
            total = sum(f.get("runs", 0) for f in p.get("batting", {}).values())
            return total

    players.sort(key=sort_key, reverse=True)

    total = len(players)
    players = players[offset:offset + limit]

    # Enrich with static meta (country, role, image_url) for the 16 known players
    meta_path = os.path.join(BASE_DIR, "data", "static", "players_meta.json")
    meta_map = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            meta_map = json.load(mf)
    
    for p in players:
        m = meta_map.get(p["name"], {})
        if m:
            p["country"]   = m.get("country", "")
            p["role"]      = m.get("role", "")
            p["image_url"] = m.get("image_url", "")
            p["iso_code"]  = m.get("iso_code", "")
            p["full_name"] = m.get("full_name", p["name"])

    return jsonify({
        "total":   total,
        "offset":  offset,
        "limit":   limit,
        "players": players,
    })


@app.route("/api/players/<player_name>")
def get_player(player_name):
    """Full profile for one player by name."""
    data = load_processed("players_index.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    # Try exact match first, then case-insensitive
    player = data.get(player_name)
    if not player:
        name_lower = player_name.lower()
        for key, val in data.items():
            if key.lower() == name_lower:
                player = val
                break

    if not player:
        # Soft-miss response to avoid noisy frontend 404s for optional lookups.
        return jsonify({"error": f"Player '{player_name}' not found", "found": False}), 200

    # Attach extra data
    yearly  = load_processed("player_yearly.json") or {}
    vs_opp  = load_processed("player_vs_opp.json") or {}
    venues  = load_processed("player_venues.json") or {}

    player["yearly"]     = yearly.get(player_name, {})
    player["vs_opp"]     = vs_opp.get(player_name, {})
    player["at_venues"]  = venues.get(player_name, {})

    return jsonify(player)


# ── Teams ─────────────────────────────────────────────────────────────────────

@app.route("/api/teams")
def get_teams():
    """All teams with format stats."""
    data = load_processed("team_format_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500
    return jsonify(data)


@app.route("/api/teams/<team_name>")
def get_team(team_name):
    """Full profile for one team."""
    fmt_stats   = load_processed("team_format_stats.json") or {}
    venue_stats = load_processed("team_venue_stats.json") or {}
    h2h         = load_processed("h2h.json") or {}

    team_data = fmt_stats.get(team_name)
    if not team_data:
        # Try case-insensitive
        for key in fmt_stats:
            if key.lower() == team_name.lower():
                team_data = fmt_stats[key]
                team_name = key
                break

    if not team_data:
        # Soft-miss response to avoid noisy frontend 404s for optional lookups.
        return jsonify({"error": f"Team '{team_name}' not found", "found": False}), 200

    # Build H2H records for this team
    team_h2h = {}
    for key, record in h2h.items():
        t_a, t_b, fmt = key.split("|")
        if t_a == team_name or t_b == team_name:
            opponent = t_b if t_a == team_name else t_a
            is_team_a = (t_a == team_name)
            if opponent not in team_h2h:
                team_h2h[opponent] = {}
            team_h2h[opponent][fmt] = {
                "matches":   record["matches"],
                "won":       record["team_a_wins"] if is_team_a else record["team_b_wins"],
                "lost":      record["team_b_wins"] if is_team_a else record["team_a_wins"],
                "tied":      record["ties"],
                "no_result": record["no_result"],
                "win_pct":   record["team_a_win_pct"] if is_team_a else record["team_b_win_pct"],
                "last_result": record["last_result"],
            }

    return jsonify({
        "name":          team_name,
        "format_stats":  team_data,
        "venue_stats":   venue_stats.get(team_name, {}),
        "head_to_head":  team_h2h,
    })


# ── Venues ────────────────────────────────────────────────────────────────────

def normalize_name(name):
    if not name:
        return ''
    return re.sub(r'[^a-z0-9]+', '', name.lower())


@app.route("/api/venues")
def get_venues():
    """All venues with scoring stats."""
    data = load_processed("venue_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    search = request.args.get("search", "").lower()
    if search:
        data = {k: v for k, v in data.items() if search in k.lower()}

    return jsonify(data)


@app.route("/api/venues/<path:venue_name>")
def get_venue(venue_name):
    """Full profile for one venue."""
    stats    = load_processed("venue_stats.json") or {}
    batters  = load_processed("venue_batters.json") or {}
    bowlers  = load_processed("venue_bowlers.json") or {}

    venue = stats.get(venue_name)
    if not venue:
        query_key = normalize_name(venue_name)
        for key in stats:
            if normalize_name(key) == query_key:
                venue = stats[key]
                venue_name = key
                break

    if not venue:
        query_key = normalize_name(venue_name)
        for key in stats:
            if query_key and query_key in normalize_name(key):
                venue = stats[key]
                venue_name = key
                break

    if not venue:
        # Soft-miss response to avoid noisy frontend 404s for optional context lookups.
        return jsonify({"error": f"Venue '{venue_name}' not found", "found": False}), 200

    venue["top_batters"] = batters.get(venue_name, [])
    venue["top_bowlers"] = bowlers.get(venue_name, [])

    return jsonify(venue)


@app.route("/api/team-venue-stats")
def get_team_venue_stats():
    """All teams' venue-wise records by format."""
    data = load_processed("team_venue_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500
    return jsonify(data)


# ── Rankings ──────────────────────────────────────────────────────────────────

@app.route("/api/rankings")
def get_rankings():
    """
    Returns players ranked by a stat.
    Query params:
        format  — Test / ODI / T20I  (required)
        type    — batting / bowling   (default: batting)
        limit   — number of results   (default: 10)
    """
    fmt   = request.args.get("format", "T20I")
    rtype = request.args.get("type", "batting")
    limit = int(request.args.get("limit", 10))

    data = load_processed("players_index.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    results = []
    for name, player in data.items():
        if rtype == "batting":
            stats = player.get("batting", {}).get(fmt)
            if stats and stats.get("innings", 0) >= 5:
                results.append({
                    "player":    name,
                    "matches":   stats["matches"],
                    "innings":   stats["innings"],
                    "runs":      stats["runs"],
                    "average":   stats["average"],
                    "strike_rate": stats["strike_rate"],
                    "hundreds":  stats["hundreds"],
                    "fifties":   stats["fifties"],
                    "highest":   stats["highest"],
                })
        else:  # bowling
            stats = player.get("bowling", {}).get(fmt)
            if stats and stats.get("wickets", 0) >= 5:
                results.append({
                    "player":   name,
                    "matches":  stats["matches"],
                    "wickets":  stats["wickets"],
                    "average":  stats["average"],
                    "economy":  stats["economy"],
                    "five_wkts": stats["five_wkts"],
                })

    sort_key = "runs" if rtype == "batting" else "wickets"
    results.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    return jsonify({
        "format":  fmt,
        "type":    rtype,
        "results": results[:limit],
    })


# ── Records ───────────────────────────────────────────────────────────────────

@app.route("/api/records")
def get_records():
    """All-time records, enriched with country from players_index."""
    data = load_processed("records.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    # Enrich each player entry with their country from players_index
    players_index = load_processed("players_index.json") or {}
    country_map = {name: info.get("country", "") for name, info in players_index.items()}

    def enrich_list(lst):
        for entry in (lst or []):
            if "player" in entry and not entry.get("country"):
                entry["country"] = country_map.get(entry["player"], "")
        return lst

    for cat in ("most_runs", "most_wickets", "best_averages", "most_hundreds"):
        if cat in data:
            for fmt in ("Test", "ODI", "T20I"):
                enrich_list(data[cat].get(fmt))

    # Provide explicit sidebar payload so frontend does not synthesize
    # section cards from unrelated fallback/static rows.
    sidebar = {
        "all_time_bests": [],
        "records_by_country": [],
        "recently_broken": [],
    }

    def _num(entry, key):
        val = (entry or {}).get(key)
        try:
            return float(val)
        except (TypeError, ValueError):
            return -1.0

    provided_sidebar = data.get("sidebar") if isinstance(data.get("sidebar"), dict) else {}

    # 1) All-Time Bests: use provided payload if present, otherwise derive a canonical list.
    all_time = provided_sidebar.get("all_time_bests")
    if isinstance(all_time, list) and all_time:
        sidebar["all_time_bests"] = all_time
    else:
        picks = [
            ("Most Test runs ever", "most_runs", "Test", "runs"),
            ("Most Test wickets", "most_wickets", "Test", "wickets"),
            ("Highest Test average", "best_averages", "Test", "average"),
            ("Most ODI runs", "most_runs", "ODI", "runs"),
            ("Most ODI centuries", "most_hundreds", "ODI", "hundreds"),
            ("Most T20I runs", "most_runs", "T20I", "runs"),
        ]
        for label, cat, fmt, metric in picks:
            rows = ((data.get(cat) or {}).get(fmt) or [])
            if not rows:
                continue
            top = sorted(rows, key=lambda e: _num(e, metric), reverse=True)[0]
            sidebar["all_time_bests"].append({
                "name": top.get("player") or top.get("name") or "",
                "country": top.get("country", ""),
                "label": label,
                "value": top.get(metric),
                "type": "player",
            })

    # 2) Records by Country: prefer provided payload, else count enriched top-list entries.
    by_country = provided_sidebar.get("records_by_country")
    if isinstance(by_country, list) and by_country:
        sidebar["records_by_country"] = by_country
    else:
        counts = {}
        for cat in ("most_runs", "most_wickets", "best_averages", "most_hundreds"):
            by_fmt = data.get(cat) or {}
            for fmt in ("Test", "ODI", "T20I"):
                for entry in (by_fmt.get(fmt) or []):
                    c = entry.get("country") or ""
                    if c:
                        counts[c] = counts.get(c, 0) + 1
        top_countries = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        sidebar["records_by_country"] = [
            {
                "country": country,
                "count": count,
                "label": f"{count} record entries in top lists",
                "type": "team",
            }
            for country, count in top_countries
        ]

    # 3) Recently Broken: only use explicit data when present (no synthetic fallback).
    recent = provided_sidebar.get("recently_broken")
    if isinstance(recent, list):
        sidebar["recently_broken"] = recent

    data["sidebar"] = sidebar

    return jsonify(data)


# ── H2H ──────────────────────────────────────────────────────────────────────

@app.route("/api/h2h")
def get_h2h():
    """
    Head-to-head between two teams.
    Query params: team_a, team_b, format (optional)
    """
    team_a = request.args.get("team_a", "")
    team_b = request.args.get("team_b", "")
    fmt    = request.args.get("format")

    if not team_a or not team_b:
        return jsonify({"error": "team_a and team_b are required"}), 400

    data = load_processed("h2h.json") or {}
    t_a, t_b = sorted([team_a, team_b])

    results = {}
    for key, record in data.items():
        parts = key.split("|")
        if len(parts) != 3:
            continue
        ka, kb, kf = parts
        if ka == t_a and kb == t_b:
            if not fmt or kf == fmt:
                results[kf] = record

    if not results:
        # Soft-miss response for optional sidebar context.
        return jsonify({"error": f"No H2H data found for {team_a} vs {team_b}", "found": False}), 200

    return jsonify(results)


# ── Compare ───────────────────────────────────────────────────────────────────

@app.route("/api/compare/players")
def compare_players():
    """
    Side-by-side player comparison.
    Query params: player_a, player_b
    """
    pa = request.args.get("player_a", "")
    pb = request.args.get("player_b", "")

    if not pa or not pb:
        return jsonify({"error": "player_a and player_b are required"}), 400

    data = load_processed("players_index.json") or {}

    def find_player(name):
        p = data.get(name)
        if not p:
            nl = name.lower()
            for k, v in data.items():
                if k.lower() == nl:
                    return v
        return p

    player_a = find_player(pa)
    player_b = find_player(pb)

    if not player_a:
        return jsonify({"error": f"Player '{pa}' not found", "found": False}), 200
    if not player_b:
        return jsonify({"error": f"Player '{pb}' not found", "found": False}), 200

    return jsonify({"player_a": player_a, "player_b": player_b})


# ── Search ────────────────────────────────────────────────────────────────────

@app.route("/api/search")
def search():
    """
    Global search across players, teams, venues, and matches.
    Query params: q (search term), limit (default 20)
    """
    q     = request.args.get("q", "").lower().strip()
    limit = int(request.args.get("limit", 20))

    if not q or len(q) < 2:
        return jsonify({"players": [], "teams": [], "venues": [], "matches": []})

    players_data = load_processed("players_index.json") or {}
    teams_data   = load_processed("team_format_stats.json") or {}
    venues_data  = load_processed("venue_stats.json") or {}
    live_data    = load_live("matches.json") or {}
    completed_data = load_processed("completed_matches.json") or {}

    def normalize_text(value):
        return re.sub(r"\s+", " ", str(value or "").lower()).strip()

    def extract_team_pair(query_text):
        cleaned = normalize_text(query_text)
        match = re.match(r"^(.+?)\s+(?:vs|v|versus)\s+(.+?)$", cleaned)
        if not match:
            return None
        left = normalize_text(match.group(1))
        right = normalize_text(match.group(2))
        if not left or not right:
            return None
        return (left, right)

    query_pair = extract_team_pair(q)

    def pair_matches(match_t1, match_t2):
        if not query_pair:
            return False
        team_a = normalize_text(match_t1)
        team_b = normalize_text(match_t2)
        return (
            (query_pair[0] == team_a and query_pair[1] == team_b) or
            (query_pair[0] == team_b and query_pair[1] == team_a)
        )

    def search_score(match):
        name = normalize_text(match.get("name"))
        t1 = normalize_text(match.get("t1") or match.get("team1"))
        t2 = normalize_text(match.get("t2") or match.get("team2"))
        teams = normalize_text(" ".join(match.get("teams") or []))
        venue = normalize_text(match.get("venue"))
        series = normalize_text(match.get("series") or match.get("series_id"))
        status = normalize_text(match.get("status"))
        date = normalize_text(match.get("date") or match.get("dateTimeGMT"))
        match_type = normalize_text(match.get("matchType") or match.get("type") or match.get("format"))
        score_text = normalize_text(match.get("scoreText") or summarize_match_score(match))
        blob = " ".join([name, t1, t2, teams, venue, series, status, date, match_type, score_text])

        if q not in blob and not pair_matches(t1, t2):
            return None

        score = 0
        if q == date or q in date:
            score += 100
        if q == name or q == f"{t1} vs {t2}" or q == f"{t2} vs {t1}" or pair_matches(t1, t2):
            score += 90
        if q in score_text:
            score += 70
        if q in status:
            score += 60
        if q in venue or q in series:
            score += 30
        if q in teams or q in t1 or q in t2:
            score += 80

        return {
            "id": match.get("id") or match.get("unique_id") or "",
            "name": match.get("name") or f"{match.get('t1') or match.get('team1') or ''} vs {match.get('t2') or match.get('team2') or ''}",
            "t1": match.get("t1") or match.get("team1") or (match.get("teams") or [""])[0],
            "t2": match.get("t2") or match.get("team2") or (match.get("teams") or ["", ""])[1],
            "team1": match.get("team1") or match.get("t1") or (match.get("teams") or [""])[0],
            "team2": match.get("team2") or match.get("t2") or (match.get("teams") or ["", ""])[1],
            "teams": match.get("teams") or [match.get("t1") or match.get("team1") or "", match.get("t2") or match.get("team2") or ""],
            "matchType": match.get("matchType") or match.get("type") or match.get("format") or "",
            "date": match.get("date") or match.get("dateTimeGMT") or "",
            "venue": match.get("venue") or "",
            "status": match.get("status") or "",
            "series": match.get("series") or match.get("series_id") or "",
            "scoreText": match.get("scoreText") or summarize_match_score(match),
            "matchEnded": bool(match.get("matchEnded")),
            "matchStarted": bool(match.get("matchStarted")),
            "_score": score,
        }

    # Search players
    matched_players = []
    for name, player in players_data.items():
        if q in name.lower():
            total_runs = sum(f.get("runs", 0) for f in player.get("batting", {}).values())
            total_wkts = sum(f.get("wickets", 0) for f in player.get("bowling", {}).values())
            matched_players.append({
                "name":    name,
                "formats": player.get("formats", []),
                "runs":    total_runs,
                "wickets": total_wkts,
            })
    matched_players.sort(key=lambda x: x["runs"] + x["wickets"] * 20, reverse=True)

    # Search teams
    matched_teams = [
        {"name": name, "formats": list(stats.keys())}
        for name, stats in teams_data.items()
        if q in name.lower()
    ]

    # Search venues
    matched_venues = [
        {"name": name, "matches": stats.get("matches", 0)}
        for name, stats in venues_data.items()
        if q in name.lower()
    ]
    matched_venues.sort(key=lambda x: x["matches"], reverse=True)

    # Search matches across live/upcoming and completed fixtures.
    all_matches = []
    all_matches.extend((live_data or {}).get("data") or (live_data or {}).get("matches") or [])
    all_matches.extend((completed_data or {}).get("data") or [])

    seen_match_ids = set()
    matched_matches = []
    for match in all_matches:
        if not isinstance(match, dict):
            continue
        match_id = str(match.get("id") or match.get("unique_id") or "").strip()
        if match_id and match_id in seen_match_ids:
            continue
        result = search_score(match)
        if not result:
            continue
        if match_id:
            seen_match_ids.add(match_id)
        matched_matches.append(result)

    matched_matches.sort(
        key=lambda item: (
            -item.get("_score", 0),
            item.get("date") or "",
            item.get("name") or "",
        )
    )

    return jsonify({
        "query":   q,
        "players": matched_players[:limit],
        "teams":   matched_teams[:limit],
        "venues":  matched_venues[:limit],
        "matches": matched_matches,
    })


# ── Venue insights (for Home/Matches sidebar) ─────────────────────────────────

@app.route("/api/insights")
def get_insights():
    """Pre-computed venue insights for the Home page sidebar panel."""
    data = load_processed("venue_insights.json")
    if data is None:
        return jsonify({}), 500

    venue = request.args.get("venue")
    if venue:
        # Return insights for a specific venue
        for key in data:
            if venue.lower() in key.lower():
                return jsonify({key: data[key]})
        return jsonify({})

    # Return top 5 venues by matches
    venue_stats = load_processed("venue_stats.json") or {}
    top_venues = sorted(venue_stats.keys(),
                        key=lambda v: venue_stats[v].get("matches", 0),
                        reverse=True)[:5]

    return jsonify({v: data[v] for v in top_venues if v in data})


# ════════════════════════════════════════════════════════════════════════════
# SOURCE A ENDPOINTS — CricAPI live data
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/live")
def get_live():
    """Live match scores. Falls back to sample cache if API returns empty."""
    data = fetch_cricapi("currentMatches", cache_file="live.json", max_age_minutes=LIVE_CACHE_TTL_MINUTES)
    matches = (data or {}).get("data") or (data or {}).get("matches") or []
    if not matches:
        cached = load_live("live.json")
        matches = (cached or {}).get("data") or (cached or {}).get("matches") or []

    # Enrich live/in-progress matches with per-match scorecards when available.
    # Free plan safety: attempt enrichment for only one active match.
    # Also enforce a strict daily gate for any scorecard API call.
    # CricAPI currentMatches can omit innings score for some fixtures.
    max_scorecard_calls = 1
    scorecard_calls = 0
    daily_scorecard_gate_file = "scorecard_daily_gate.json"
    can_call_scorecard_today = cache_age_minutes(daily_scorecard_gate_file) >= 1440
    info = (data or {}).get("info") if isinstance(data, dict) else None
    if isinstance(info, dict):
        used = int(info.get("hitsUsed") or info.get("hitsToday") or 0)
        limit = int(info.get("hitsLimit") or 0)
        if limit and used >= max(0, limit - 3):
            max_scorecard_calls = 0

    for m in matches:
        if not isinstance(m, dict):
            continue
        if not m.get("matchStarted"):
            continue
        if m.get("matchEnded"):
            continue
        if (m.get("score") or []):
            continue

        # Only enrich one active match per request to protect API credits.
        if scorecard_calls >= max_scorecard_calls:
            break

        # Hard-stop: at most one scorecard API call per day.
        if not can_call_scorecard_today:
            break

        mid = str(m.get("id") or m.get("unique_id") or "").strip()
        if not mid:
            continue

        # Prefer already-cached per-match scorecard before making a live API call.
        cached_sc = load_live(f"score_{mid}.json")
        cached_sc_data = (cached_sc or {}).get("data") if isinstance(cached_sc, dict) else None
        if isinstance(cached_sc_data, dict):
            cached_score = cached_sc_data.get("score") or []
            if cached_score:
                m["score"] = cached_score
                if cached_sc_data.get("t1s") and not m.get("t1s"):
                    m["t1s"] = cached_sc_data.get("t1s")
                if cached_sc_data.get("t2s") and not m.get("t2s"):
                    m["t2s"] = cached_sc_data.get("t2s")
                continue

        sc = fetch_cricapi(
            "match_scorecard",
            params={"id": mid},
            cache_file=f"score_{mid}.json",
            max_age_minutes=SCORECARD_CACHE_TTL_MINUTES,
        )
        scorecard_calls += 1
        if scorecard_calls == 1:
            save_live(daily_scorecard_gate_file, {
                "last_call_at": datetime.now().isoformat(),
                "match_id": mid,
            })
        # Stop further scorecard calls if provider quota is exceeded.
        if isinstance(sc, dict) and sc.get("status") == "failure":
            reason = str(sc.get("reason") or "").lower()
            if "hits" in reason and "exceed" in reason:
                break
            continue

        sc_data = (sc or {}).get("data") if isinstance(sc, dict) else None
        if isinstance(sc_data, dict):
            sc_score = sc_data.get("score") or []
            if sc_score:
                m["score"] = sc_score
            if sc_data.get("t1s") and not m.get("t1s"):
                m["t1s"] = sc_data.get("t1s")
            if sc_data.get("t2s") and not m.get("t2s"):
                m["t2s"] = sc_data.get("t2s")
    return jsonify({"data": matches})


@app.route("/api/matches")
def get_matches():
    """Fixtures: live, upcoming, and completed matches.
    
    Combines:
    - Live/upcoming from CricAPI (max 1440 min cache)
    - Completed matches from Cricsheet (processed data)
    """
    # Get live/upcoming matches from CricAPI
    data = fetch_cricapi("matches", cache_file="matches.json", max_age_minutes=MATCH_LIST_CACHE_TTL_MINUTES)
    live_upcoming = (data or {}).get("data") or (data or {}).get("matches") or []
    if not live_upcoming:
        cached = load_live("matches.json")
        live_upcoming = (cached or {}).get("data") or (cached or {}).get("matches") or []
    
    # Get completed matches from Cricsheet
    completed_data = load_processed("completed_matches.json")
    completed = (completed_data or {}).get("data") or []
    
    # Merge all matches
    all_matches = live_upcoming + completed
    
    return jsonify({"data": all_matches})


@app.route("/api/matches/<match_id>")
def get_match(match_id):
    """Individual match detail. Searches live/upcoming and completed matches."""
    completed_data = load_processed("completed_matches.json")
    if completed_data:
        completed = completed_data.get("data") or []
        for m in completed:
            if str(m.get("id") or m.get("unique_id") or "") == str(match_id):
                return jsonify({"data": augment_completed_match(m)})

    cache_file = f"match_{match_id}.json"
    data = fetch_cricapi("match_info", params={"id": match_id},
                         cache_file=cache_file, max_age_minutes=MATCH_INFO_CACHE_TTL_MINUTES)
    if data:
        return jsonify(data)
    
    # Search the cached live/upcoming matches list for this ID
    cached = load_live("matches.json")
    if cached:
        matches = cached.get("data") or cached.get("matches") or []
        for m in matches:
            if str(m.get("id") or m.get("unique_id") or "") == str(match_id):
                return jsonify({"data": m})
    
    return jsonify({"error": "Match not found"}), 404


@app.route("/api/matches/<match_id>/score")
def get_match_score(match_id):
    """Live scorecard. Falls back to cached matches and completed matches."""
    completed_data = load_processed("completed_matches.json")
    if completed_data:
        completed = completed_data.get("data") or []
        for m in completed:
            if str(m.get("id") or m.get("unique_id") or "") == str(match_id):
                return jsonify({"data": augment_completed_match(m)})

    cache_file = f"score_{match_id}.json"
    data = fetch_cricapi("match_scorecard", params={"id": match_id},
                         cache_file=cache_file, max_age_minutes=SCORECARD_CACHE_TTL_MINUTES)
    if data:
        return jsonify(data)
    
    # Try to find basic score info from cached live/upcoming matches
    cached = load_live("matches.json")
    if cached:
        matches = cached.get("data") or cached.get("matches") or []
        for m in matches:
            if str(m.get("id") or m.get("unique_id") or "") == str(match_id):
                return jsonify({"data": m})
    
    return jsonify({"error": "Score not found"}), 404


@app.route("/api/series")
def get_series():
    """Active series list. Returns cached data if CricAPI unavailable."""
    try:
        data = fetch_cricapi("series", cache_file="series.json", max_age_minutes=SERIES_CACHE_TTL_MINUTES)
        if data:
            series = data.get("data") or data.get("series") or data.get("series_list") or []
            return jsonify({"data": series})
        cached = load_live("series.json")
        if cached:
            series = cached.get("data") or cached.get("series") or cached.get("series_list") or []
            return jsonify({"data": series, "cached": True})
        return jsonify({"data": [], "note": "No series data available"})
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# UTILITY
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
def status():
    """Health check — shows which data files are available."""
    files = [
        "players_index.json", "player_yearly.json", "player_vs_opp.json",
        "player_venues.json", "h2h.json", "team_format_stats.json",
        "team_venue_stats.json", "venue_stats.json", "venue_batters.json",
        "venue_bowlers.json", "venue_insights.json", "records.json",
        "completed_matches.json"
    ]
    status_data = {}
    for f in files:
        path = os.path.join(PROCESSED_DIR, f)
        root_path = os.path.join(BASE_DIR, f)
        
        if os.path.exists(path):
            size_kb = round(os.path.getsize(path) / 1024, 1)
            status_data[f] = {"exists": True, "location": "data/processed", "size_kb": size_kb}
        elif os.path.exists(root_path):
            size_kb = round(os.path.getsize(root_path) / 1024, 1)
            status_data[f] = {"exists": True, "location": "root", "size_kb": size_kb}
        else:
            status_data[f] = {"exists": False}

    live_files = os.listdir(LIVE_DIR) if os.path.exists(LIVE_DIR) else []

    return jsonify({
        "status":        "ok",
        "cricapi_key":   "set" if CRICAPI_KEY != "YOUR_CRICAPI_KEY_HERE" else "not set",
        "processed":     status_data,
        "live_cache":    live_files,
        "timestamp":     datetime.now().isoformat(),
    })


@app.after_request
def add_cors(response):
    """Allow frontend JS to call the API from the same origin."""
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response




@app.route("/api/icc-rankings")
def get_icc_rankings():
    category = request.args.get("category", "batting")
    fmt      = request.args.get("format", "T20I")
    try:
        from scrape_rankings import get_current_rankings, build_hardcoded_rankings
        data = get_current_rankings()
        # If cached file was empty, force use hardcoded fallback
        if data:
            if category == "teams":
                check = data.get("team", {}).get(fmt, [])
            else:
                check = data.get("player", {}).get(category, {}).get(fmt, [])
            if not check:
                data = build_hardcoded_rankings()
        else:
            data = build_hardcoded_rankings()
    except Exception as e:
        print(f"  rankings error: {e}")
        data = None

    if not data:
        return jsonify({"category": category, "format": fmt, "rankings": []}), 200

    if category == "teams":
        result = data.get("team", {}).get(fmt, [])
    else:
        result = data.get("player", {}).get(category, {}).get(fmt, [])

    return jsonify({
        "category": category,
        "format": fmt,
        "scraped_at": data.get("scraped_at", ""),
        "source":     data.get("source", "hardcoded_fallback"),
        "rankings":   result or []
    })

@app.route("/api/meta/players")
def get_players_meta():
    path = os.path.join(STATIC_DIR, "players_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/meta/players/<player_name>")
def get_player_meta(player_name):
    path = os.path.join(STATIC_DIR, "players_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 500
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    meta = data.get(player_name)
    if not meta:
        for key, val in data.items():
            if player_name.lower() in key.lower() or player_name.lower() in val.get("full_name","").lower():
                return jsonify(val)
        return jsonify({"error": f"No meta for '{player_name}'", "found": False}), 200
    return jsonify(meta)

@app.route("/api/meta/teams")
def get_teams_meta():
    path = os.path.join(STATIC_DIR, "teams_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/meta/venues")
def get_venues_meta():
    path = os.path.join(STATIC_DIR, "venues_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))


# ════════════════════════════════════════════════════════════════════════════
# ML PROBABILITY PREDICTION ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.route("/api/predict/player/<player_name>")
def predict_player(player_name):
    """
    Get probability predictions for a player.
    Query params:
        metric — 50 / 100 / wicket_maiden / strike_rate>140 / avg>50
        format — Test / ODI / T20I (default: ODI)
    """
    if not ml_engine:
        return jsonify({"error": "ML engine not initialized"}), 503

    metric = request.args.get("metric", "50")
    format = request.args.get("format", "ODI")

    try:
        result = ml_engine.player_performance_likelihood(player_name, metric, format)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/player/<player_name>/all")
def predict_player_all(player_name):
    """
    Get all probability predictions for a player across metrics.
    Query params:
        format — Test / ODI / T20I (default: ODI)
    """
    if not ml_engine:
        return jsonify({"error": "ML engine not initialized"}), 503

    format = request.args.get("format", "ODI")

    try:
        metrics = ["50", "100", "wicket_maiden", "strike_rate>140", "avg>50"]
        results = {}
        for metric in metrics:
            results[metric] = ml_engine.player_performance_likelihood(
                player_name, metric, format
            )
        return jsonify({
            "player": player_name,
            "format": format,
            "predictions": results,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/team_match", methods=["POST"])
def predict_team_match():
    """
    Predict match outcome between two teams.
    Request body:
        {
            "team_a": "India",
            "team_b": "Australia",
            "format": "ODI",
            "venue": "MCG" (optional)
        }
    """
    if not ml_engine:
        return jsonify({"error": "ML engine not initialized"}), 503

    data = request.get_json() or {}
    team_a = data.get("team_a", "")
    team_b = data.get("team_b", "")
    format = data.get("format", "ODI")
    venue = data.get("venue")

    if not team_a or not team_b:
        return jsonify({"error": "team_a and team_b required"}), 400

    try:
        result = ml_engine.team_match_outcome(team_a, team_b, format, venue)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/venue/<venue_name>")
def predict_venue(venue_name):
    """
    Get venue performance bias and probabilities.
    Query params:
        team — team name (optional)
        format — Test / ODI / T20I (default: ODI)
    """
    if not ml_engine:
        return jsonify({"error": "ML engine not initialized"}), 503

    team = request.args.get("team")
    format = request.args.get("format", "ODI")

    try:
        result = ml_engine.venue_performance_bias(venue_name, team, format)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/leaderboard")
def predict_leaderboard():
    """
    Get top players by probability of achieving a metric.
    Query params:
        metric — 50 / 100 / wicket_maiden / strike_rate>140 / avg>50 (default: 50)
        format — Test / ODI / T20I (default: ODI)
        limit — number of results (default: 10)
    """
    if not ml_engine:
        return jsonify({"error": "ML engine not initialized"}), 503

    metric = request.args.get("metric", "50")
    format = request.args.get("format", "ODI")
    limit = int(request.args.get("limit", 10))

    try:
        result = ml_engine.leaderboard_predictions(format, metric, limit)
        return jsonify({
            "metric": metric,
            "format": format,
            "limit": limit,
            "predictions": result,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict/status")
def predict_status():
    """Check ML engine status."""
    return jsonify({
        "engine_active": ml_engine is not None,
        "timestamp": datetime.now().isoformat(),
    })


# ════════════════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("  Cricklytics Flask Backend")
    print("=" * 55)
    print(f"  Processed data : {PROCESSED_DIR}")
    print(f"  Live cache     : {LIVE_DIR}")
    print(f"  CricAPI key    : {'set ✓' if CRICAPI_KEY != 'YOUR_CRICAPI_KEY_HERE' else 'NOT SET (live endpoints disabled)'}")
    print()
    print("  Open in browser: http://localhost:5000")
    print("  API status:      http://localhost:5000/api/status")
    print("=" * 55)
    port = int(os.environ.get("PORT", 5000))
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
