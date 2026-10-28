"""Existing API contracts, extracted without changing analytical behavior."""
import json
import os
import re
from datetime import datetime
from werkzeug.exceptions import Conflict
from flask import Blueprint, current_app, jsonify, request
from ..services.legacy import (
    BASE_DIR,
    CRICAPI_KEY,
    LIVE_CACHE_TTL_MINUTES,
    LIVE_DIR,
    MATCH_INFO_CACHE_TTL_MINUTES,
    MATCH_LIST_CACHE_TTL_MINUTES,
    PROCESSED_DIR,
    SCORECARD_CACHE_TTL_MINUTES,
    SERIES_CACHE_TTL_MINUTES,
    STATIC_DIR,
    augment_completed_match,
    completed_match,
    completed_summaries,
    cache_age_minutes,
    fetch_cricapi,
    load_live,
    load_processed,
    ml_engine,
    normalize_name,
    save_live,
    summarize_match_score,
)

bp = Blueprint("api", __name__)

@bp.route("/api/players")
def get_players():
    """
    All players with career stats.
    Query params:
        format    â€” filter by format: Test / ODI / T20I
        country   â€” filter by country name (partial match)
        role      â€” bat / bowl / all (default: all)
        search    â€” search by name (partial match)
        sort      â€” runs / wickets / avg / sr (default: runs)
        limit     â€” number of results (default: 50)
        offset    â€” pagination offset (default: 0)
    """
    data = load_processed("players_index.json")
    if data is None:
        return jsonify({"error": "players_index.json not found â€” run process_cricsheet.py first"}), 500

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
            avgs = [(f.get("average") or 0) for f in p.get("batting", {}).values()]
            return max(avgs) if avgs else 0
        elif sort == "sr":
            srs = [(f.get("strike_rate") or 0) for f in p.get("batting", {}).values()]
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
        try:
            identity = current_app.extensions["identity_registry"].resolve("player",p["name"])
            if identity:p["identity_id"] = identity["id"]
        except Conflict:
            p["identity_status"] = "ambiguous"
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


@bp.route("/api/players/<player_name>")
def get_player(player_name):
    """Full profile by recorded name, explicit alias or stable identifier."""
    player_name, identity_id = current_app.extensions["identity_registry"].source_name("player",player_name)
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
                player_name = key
                break

    if not player:
        # Soft-miss response to avoid noisy frontend 404s for optional lookups.
        return jsonify({"error": f"Player '{player_name}' not found", "found": False}), 200

    # Attach extra data
    yearly  = load_processed("player_yearly.json") or {}
    vs_opp  = load_processed("player_vs_opp.json") or {}
    venues  = load_processed("player_venues.json") or {}

    if identity_id:player["identity_id"] = identity_id
    player["yearly"]     = yearly.get(player_name, {})
    player["vs_opp"]     = vs_opp.get(player_name, {})
    player["at_venues"]  = venues.get(player_name, {})

    return jsonify(player)


@bp.route("/api/teams")
def get_teams():
    """All teams with format stats."""
    data = load_processed("team_format_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500
    return jsonify(data)


@bp.route("/api/teams/<team_name>")
def get_team(team_name):
    """Full profile for one team."""
    team_name, identity_id = current_app.extensions["identity_registry"].source_name("team",team_name)
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
                "drawn": record.get('draws'),
                "no_result": record["no_result"],
                "win_pct":   record["team_a_win_pct"] if is_team_a else record["team_b_win_pct"],
                "last_result": record["last_result"],
            }

    return jsonify({
        **({"identity_id":identity_id} if identity_id else {}),
        "name":          team_name,
        "format_stats":  team_data,
        "venue_stats":   venue_stats.get(team_name, {}),
        "head_to_head":  team_h2h,
    })


@bp.route("/api/venues")
def get_venues():
    """All venues with scoring stats."""
    data = load_processed("venue_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    search = request.args.get("search", "").lower()
    if search:
        data = {k: v for k, v in data.items() if search in k.lower()}

    return jsonify(data)


@bp.route("/api/venues/<path:venue_name>")
def get_venue(venue_name):
    """Full profile for one venue."""
    venue_name, identity_id = current_app.extensions["identity_registry"].source_name("venue",venue_name)
    stats    = load_processed("venue_stats.json") or {}
    batters  = load_processed("venue_batters.json") or {}
    bowlers  = load_processed("venue_bowlers.json") or {}

    venue = stats.get(venue_name)
    if not venue:
        candidates=[name for name in stats if normalize_name(name)==normalize_name(venue_name)]
        if len(candidates)>1:
            from werkzeug.exceptions import Conflict
            raise Conflict('Ambiguous venue name; use a stable identity identifier')
        if candidates:venue_name=candidates[0];venue=stats[venue_name]

    if not venue:
        # Soft-miss response to avoid noisy frontend 404s for optional context lookups.
        return jsonify({"error": f"Venue '{venue_name}' not found", "found": False}), 200

    if identity_id:venue["identity_id"] = identity_id
    venue["top_batters"] = batters.get(venue_name, [])
    venue["top_bowlers"] = bowlers.get(venue_name, [])

    return jsonify(venue)


@bp.route("/api/team-venue-stats")
def get_team_venue_stats():
    """All teams' venue-wise records by format."""
    data = load_processed("team_venue_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500
    return jsonify(data)


@bp.route("/api/rankings")
def get_rankings():
    """
    Returns players ranked by a stat.
    Query params:
        format  â€” Test / ODI / T20I  (required)
        type    â€” batting / bowling   (default: batting)
        limit   â€” number of results   (default: 10)
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


@bp.route("/api/records")
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


@bp.route("/api/h2h")
def get_h2h():
    """
    Head-to-head between two teams.
    Query params: team_a, team_b, format (optional)
    """
    team_a = request.args.get("team_a", "")
    team_b = request.args.get("team_b", "")
    fmt    = request.args.get("format")
    if fmt == 'T20':
        fmt = 'T20I'

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
                oriented = dict(record)
                oriented['team_a'], oriented['team_b'] = team_a, team_b
                if team_a != ka:
                    for left, right in (('team_a_wins', 'team_b_wins'), ('team_a_win_pct', 'team_b_win_pct')):
                        oriented[left], oriented[right] = record.get(right), record.get(left)
                results[kf] = oriented

    if not results:
        # Soft-miss response for optional sidebar context.
        return jsonify({"error": f"No H2H data found for {team_a} vs {team_b}", "found": False}), 200

    return jsonify(results[fmt] if fmt else results)


@bp.route("/api/compare/players")
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
        name, _ = current_app.extensions["identity_registry"].source_name("player",name)
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


@bp.route("/api/search")
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
    completed_data = {"data": completed_summaries()}

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
        "matches": matched_matches[:limit],
    })


@bp.route("/api/insights")
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


@bp.route("/api/live")
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


@bp.route("/api/matches")
def get_matches():
    """Fixtures: live, upcoming, and completed matches.

    Combines:
    - Live/upcoming from CricAPI (max 1440 min cache)
    - Completed matches from Cricsheet (processed data)
    """
    # Get live/upcoming matches from CricAPI
    data = fetch_cricapi("matches", cache_file="matches.json", max_age_minutes=MATCH_LIST_CACHE_TTL_MINUTES)
    cached = None
    live_upcoming = (data or {}).get("data") or (data or {}).get("matches") or []
    if not live_upcoming:
        cached = load_live("matches.json")
        live_upcoming = (cached or {}).get("data") or (cached or {}).get("matches") or []

    # Get completed matches from Cricsheet
    completed = completed_summaries()

    from criclytics_app.services.match_listing import listing
    from ..services.provenance import metadata
    result = listing(live_upcoming, completed, request.args, current_app.extensions["identity_registry"])
    result['provenance'] = metadata(data or cached)
    result['provenance']['historical_source'] = 'cricsheet_legacy_processed'
    return jsonify(result)


@bp.route("/api/matches/<match_id>")
def get_match(match_id):
    """Individual match detail. Searches live/upcoming and completed matches."""
    match = completed_match(match_id)
    if match:
        return jsonify({'data': augment_completed_match(match)})

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


@bp.route("/api/matches/<match_id>/score")
def get_match_score(match_id):
    """Live scorecard. Falls back to cached matches and completed matches."""
    match = completed_match(match_id)
    if match:
        return jsonify({'data': augment_completed_match(match)})

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


@bp.route("/api/series")
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


@bp.get('/api/health')
def health():
    return jsonify({'status':'alive'})


@bp.get('/api/ready')
@bp.get('/api/status')
def status():
    from ..services.diagnostics import readiness
    data = readiness(current_app)
    return jsonify(data), 200 if data['ready'] else 503


@bp.route("/api/icc-rankings")
def get_icc_rankings():
    category = request.args.get("category", "batting")
    fmt      = request.args.get("format", "T20I")
    from werkzeug.exceptions import BadRequest
    from ..integrations.rankings import build_hardcoded_rankings
    from ..services.provenance import metadata
    if category not in ('teams', 'batting', 'bowling', 'allrounder'):
        raise BadRequest('Unsupported ranking category')
    data = load_live('rankings.json') or build_hardcoded_rankings()
    result = (data.get('team', {}).get(fmt, []) if category == 'teams' else
              data.get('player', {}).get(category, {}).get(fmt, []))
    stored_info = data.get('category_metadata', {}).get(category + ':' + fmt)
    info = metadata(stored_info or data)
    return jsonify({'category': category, 'format': fmt, 'rankings': result or [],
                    'provenance': info, **info})


@bp.route("/api/meta/players")
def get_players_meta():
    path = os.path.join(STATIC_DIR, "players_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))


@bp.route("/api/meta/players/<player_name>")
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


@bp.route("/api/meta/teams")
def get_teams_meta():
    path = os.path.join(STATIC_DIR, "teams_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))


@bp.route("/api/meta/venues")
def get_venues_meta():
    path = os.path.join(STATIC_DIR, "venues_meta.json")
    if not os.path.exists(path):
        return jsonify({"error": "run create_static_files.py"}), 500
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))


def unavailable_prediction(**context):
    from ..ml.probability import unavailable
    return jsonify(unavailable(**context))


@bp.route('/api/predict/player/<player_name>')
def predict_player(player_name):
    return unavailable_prediction(player=player_name, metric=request.args.get('metric', '50'),
                                  format=request.args.get('format', 'ODI'))


@bp.route('/api/predict/player/<player_name>/all')
def predict_player_all(player_name):
    return unavailable_prediction(player=player_name, format=request.args.get('format', 'ODI'), predictions={})


@bp.route('/api/predict/team_match', methods=['POST'])
def predict_team_match():
    data = request.get_json()
    return unavailable_prediction(team_a=data['team_a'], team_b=data['team_b'],
                                  format=data.get('format', 'ODI'))


@bp.route('/api/predict/venue/<venue_name>')
def predict_venue(venue_name):
    return unavailable_prediction(venue=venue_name, format=request.args.get('format', 'ODI'))


@bp.route('/api/predict/leaderboard')
def predict_leaderboard():
    return unavailable_prediction(predictions=[], evaluated_players=0,
                                  metric=request.args.get('metric', '50'),
                                  format=request.args.get('format', 'ODI'))


@bp.route('/api/predict/status')
def predict_status():
    return unavailable_prediction(engine_active=False)


@bp.get('/api/coverage')
def dataset_coverage():
    from ..services.repository import safe_file
    coverage = current_app.extensions['json_repository'].read(safe_file(PROCESSED_DIR,'coverage.json'))
    if not coverage:
        return jsonify({'available':False,'dataset_id':None,'data_cutoff':None,
                        'scope':'Legacy historical subset; exact coverage metadata unavailable'})
    manifest = current_app.extensions['json_repository'].read(safe_file(PROCESSED_DIR,'manifest.json')) or {}
    return jsonify({'available':True,'dataset_id':manifest.get('dataset_id'),**coverage})


@bp.get('/api/identities/<kind>/<identifier>')
def identity_record(kind,identifier):
    from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable
    if kind not in ('player','team','venue','match'):raise BadRequest('Unsupported identity kind')
    registry=current_app.extensions['identity_registry']
    if not registry.data:raise ServiceUnavailable('Identity registry unavailable for this dataset')
    item=registry.resolve(kind,identifier)
    if not item:raise NotFound('Identity not found')
    return jsonify({'dataset_id':registry.data['dataset_id'],'identity':item})
