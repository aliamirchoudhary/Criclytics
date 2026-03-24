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
import time
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, abort
from dotenv import load_dotenv
load_dotenv()

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=".", static_url_path="")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
LIVE_DIR      = os.path.join(BASE_DIR, "data", "live")
STATIC_DIR = os.path.join(BASE_DIR, "data", "static")
os.makedirs(LIVE_DIR, exist_ok=True)

# ── CricAPI config ────────────────────────────────────────────────────────────
# Replace with your actual key from cricapi.com
CRICAPI_KEY  = os.environ.get("CRICAPI_KEY", "")
CRICAPI_BASE = "https://api.cricapi.com/v1"

# ── Helper: load a processed JSON file ───────────────────────────────────────
def load_processed(filename):
    path = os.path.join(PROCESSED_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ── Helper: load a live cache file ───────────────────────────────────────────
def load_live(filename):
    path = os.path.join(LIVE_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_live(filename, data):
    path = os.path.join(LIVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def cache_age_minutes(filename):
    """Returns how many minutes ago a live cache file was written."""
    path = os.path.join(LIVE_DIR, filename)
    if not os.path.exists(path):
        return 9999
    age = time.time() - os.path.getmtime(path)
    return age / 60

# ── CricAPI fetch with caching ────────────────────────────────────────────────
def fetch_cricapi(endpoint, params=None, cache_file=None, max_age_minutes=60):
    """
    Fetch from CricAPI. Serves from cache if fresh enough.
    max_age_minutes: how old the cache can be before re-fetching.
    """
    if cache_file and cache_age_minutes(cache_file) < max_age_minutes:
        cached = load_live(cache_file)
        if cached:
            return cached

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
        if cache_file:
            save_live(cache_file, data)
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
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    """Serve any HTML, CSS, JS, or image file from the project root."""
    return send_from_directory(BASE_DIR, filename)


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
        return jsonify({"error": f"Player '{player_name}' not found"}), 404

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
        return jsonify({"error": f"Team '{team_name}' not found"}), 404

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
        # Try partial match
        for key in stats:
            if venue_name.lower() in key.lower():
                venue = stats[key]
                venue_name = key
                break

    if not venue:
        return jsonify({"error": f"Venue '{venue_name}' not found"}), 404

    venue["top_batters"] = batters.get(venue_name, [])
    venue["top_bowlers"] = bowlers.get(venue_name, [])

    return jsonify(venue)


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
        return jsonify({"error": f"No H2H data found for {team_a} vs {team_b}"}), 404

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
        return jsonify({"error": f"Player '{pa}' not found"}), 404
    if not player_b:
        return jsonify({"error": f"Player '{pb}' not found"}), 404

    return jsonify({"player_a": player_a, "player_b": player_b})


# ── Search ────────────────────────────────────────────────────────────────────

@app.route("/api/search")
def search():
    """
    Global search across players, teams, venues.
    Query params: q (search term), limit (default 20)
    """
    q     = request.args.get("q", "").lower().strip()
    limit = int(request.args.get("limit", 20))

    if not q or len(q) < 2:
        return jsonify({"players": [], "teams": [], "venues": []})

    players_data = load_processed("players_index.json") or {}
    teams_data   = load_processed("team_format_stats.json") or {}
    venues_data  = load_processed("venue_stats.json") or {}

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

    return jsonify({
        "query":   q,
        "players": matched_players[:limit],
        "teams":   matched_teams[:limit],
        "venues":  matched_venues[:limit],
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
        return jsonify({}), 404

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
    data = fetch_cricapi("currentMatches", cache_file="live.json", max_age_minutes=60)
    matches = (data or {}).get("data") or (data or {}).get("matches") or []
    if not matches:
        cached = load_live("live.json")
        matches = (cached or {}).get("data") or (cached or {}).get("matches") or []
    return jsonify({"data": matches})


@app.route("/api/matches")
def get_matches():
    """Fixtures. Falls back to sample cache if API returns empty."""
    data = fetch_cricapi("matches", cache_file="matches.json", max_age_minutes=1440)
    matches = (data or {}).get("data") or (data or {}).get("matches") or []
    if not matches:
        cached = load_live("matches.json")
        matches = (cached or {}).get("data") or (cached or {}).get("matches") or []
    return jsonify({"data": matches})


@app.route("/api/matches/<match_id>")
def get_match(match_id):
    """Individual match detail. Falls back to cached matches."""
    cache_file = f"match_{match_id}.json"
    data = fetch_cricapi("match", params={"unique_id": match_id},
                         cache_file=cache_file, max_age_minutes=60)
    if data:
        return jsonify(data)
    # Search the cached matches list for this ID
    cached = load_live("matches.json")
    if cached:
        matches = cached.get("data") or cached.get("matches") or []
        for m in matches:
            if str(m.get("id") or m.get("unique_id") or "") == str(match_id):
                return jsonify({"data": m})
    return jsonify({"error": "Match not found"}), 404


@app.route("/api/matches/<match_id>/score")
def get_match_score(match_id):
    """Live scorecard. Falls back to cached matches."""
    cache_file = f"score_{match_id}.json"
    data = fetch_cricapi("matchScore", params={"unique_id": match_id},
                         cache_file=cache_file, max_age_minutes=60)
    if data:
        return jsonify(data)
    # Try to find basic score info from cached matches
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
    data = fetch_cricapi("series", cache_file="series.json", max_age_minutes=1440)
    if data:
        series = data.get("data") or data.get("series") or data.get("series_list") or []
        return jsonify({"data": series})
    cached = load_live("series.json")
    if cached:
        series = cached.get("data") or cached.get("series") or cached.get("series_list") or []
        return jsonify({"data": series, "cached": True})
    return jsonify({"data": [], "note": "No series data available"})


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
    ]
    status_data = {}
    for f in files:
        path = os.path.join(PROCESSED_DIR, f)
        if os.path.exists(path):
            size_kb = round(os.path.getsize(path) / 1024, 1)
            status_data[f] = {"exists": True, "size_kb": size_kb}
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
        return jsonify({"error": f"No meta for '{player_name}'"}), 404
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
    app.run(debug=True, port=5000)
