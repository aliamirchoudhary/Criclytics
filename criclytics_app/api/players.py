"""Players API contracts."""

import json
import os
import re
from werkzeug.exceptions import Conflict
from flask import current_app, jsonify, request
from ..services.legacy import (
    BASE_DIR,
    completed_summaries,
    load_live,
    load_processed,
    summarize_match_score,
)


from .blueprint import bp


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
    store = current_app.extensions["player_id_store"]
    if store:
        return jsonify(store.listing(request.args))
    data = load_processed("players_index.json")
    if data is None:
        return jsonify(
            {"error": "players_index.json not found â€” run process_cricsheet.py first"}
        ), 500

    fmt = request.args.get("format")
    country = request.args.get("country", "").lower()
    role = request.args.get("role", "all").lower()
    search = request.args.get("search", "").lower()
    sort = request.args.get("sort", "runs")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    players = list(data.values())

    # Filter by format
    if fmt:
        players = [p for p in players if fmt in p.get("formats", [])]

    # Filter by name search
    if search:
        players = [p for p in players if search in p["name"].lower()]

    # Filter by country (now stored directly on player from Cricsheet)
    if country:
        players = [
            p for p in players if country in (p.get("country", "") or "").lower()
        ]

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
    players = players[offset : offset + limit]

    # Enrich with static meta (country, role, image_url) for the 16 known players
    meta_path = os.path.join(BASE_DIR, "data", "static", "players_meta.json")
    meta_map = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as mf:
            meta_map = json.load(mf)

    for p in players:
        try:
            identity = current_app.extensions["identity_registry"].resolve(
                "player", p["name"]
            )
            if identity:
                p["identity_id"] = identity["id"]
        except Conflict:
            p["identity_status"] = "ambiguous"
        m = meta_map.get(p["name"], {})
        if m:
            p["country"] = m.get("country", "")
            p["role"] = m.get("role", "")
            p["image_url"] = m.get("image_url", "")
            p["iso_code"] = m.get("iso_code", "")
            p["full_name"] = m.get("full_name", p["name"])

    return jsonify(
        {
            "total": total,
            "offset": offset,
            "limit": limit,
            "players": players,
        }
    )


@bp.route("/api/players/<player_name>")
def get_player(player_name):
    """Full profile by recorded name, explicit alias or stable identifier."""
    store = current_app.extensions["player_id_store"]
    if store:
        return jsonify(
            store.profile(player_name) or {"found": False, "error": "Player not found"}
        )
    player_name, identity_id = current_app.extensions["identity_registry"].source_name(
        "player", player_name
    )
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
        return jsonify(
            {"error": f"Player '{player_name}' not found", "found": False}
        ), 200

    # Attach extra data
    yearly = load_processed("player_yearly.json") or {}
    vs_opp = load_processed("player_vs_opp.json") or {}
    venues = load_processed("player_venues.json") or {}

    if identity_id:
        player["identity_id"] = identity_id
    player["yearly"] = yearly.get(player_name, {})
    player["vs_opp"] = vs_opp.get(player_name, {})
    player["at_venues"] = venues.get(player_name, {})

    return jsonify(player)


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

    store = current_app.extensions["player_id_store"]
    data = {} if store else (load_processed("players_index.json") or {})

    def find_player(name):
        if store:
            return store.profile(name)
        name, _ = current_app.extensions["identity_registry"].source_name(
            "player", name
        )
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
    q = request.args.get("q", "").lower().strip()
    limit = int(request.args.get("limit", 20))

    if not q or len(q) < 2:
        return jsonify({"players": [], "teams": [], "venues": [], "matches": []})

    store = current_app.extensions["player_id_store"]
    candidates = (
        store.listing({"search": q, "limit": limit})["players"] if store else []
    )
    players_data = (
        {p["identity_id"]: p for p in candidates}
        if store
        else (load_processed("players_index.json") or {})
    )
    teams_data = load_processed("team_format_stats.json") or {}
    venues_data = load_processed("venue_stats.json") or {}
    live_data = load_live("matches.json") or {}
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
        return (query_pair[0] == team_a and query_pair[1] == team_b) or (
            query_pair[0] == team_b and query_pair[1] == team_a
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
        match_type = normalize_text(
            match.get("matchType") or match.get("type") or match.get("format")
        )
        score_text = normalize_text(
            match.get("scoreText") or summarize_match_score(match)
        )
        blob = " ".join(
            [name, t1, t2, teams, venue, series, status, date, match_type, score_text]
        )

        if q not in blob and not pair_matches(t1, t2):
            return None

        score = 0
        if q == date or q in date:
            score += 100
        if (
            q == name
            or q == f"{t1} vs {t2}"
            or q == f"{t2} vs {t1}"
            or pair_matches(t1, t2)
        ):
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
            "name": match.get("name")
            or f"{match.get('t1') or match.get('team1') or ''} vs {match.get('t2') or match.get('team2') or ''}",
            "t1": match.get("t1")
            or match.get("team1")
            or (match.get("teams") or [""])[0],
            "t2": match.get("t2")
            or match.get("team2")
            or (match.get("teams") or ["", ""])[1],
            "team1": match.get("team1")
            or match.get("t1")
            or (match.get("teams") or [""])[0],
            "team2": match.get("team2")
            or match.get("t2")
            or (match.get("teams") or ["", ""])[1],
            "teams": match.get("teams")
            or [
                match.get("t1") or match.get("team1") or "",
                match.get("t2") or match.get("team2") or "",
            ],
            "matchType": match.get("matchType")
            or match.get("type")
            or match.get("format")
            or "",
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
        if store or q in name.lower():
            total_runs = sum(
                f.get("runs", 0) for f in player.get("batting", {}).values()
            )
            total_wkts = sum(
                f.get("wickets", 0) for f in player.get("bowling", {}).values()
            )
            matched_players.append(
                {
                    "name": player["name"] if store else name,
                    **(
                        {
                            "identity_id": player["identity_id"],
                            "observed_teams": player["observed_teams"],
                        }
                        if store
                        else {}
                    ),
                    "formats": player.get("formats", []),
                    "runs": total_runs,
                    "wickets": total_wkts,
                }
            )
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
    all_matches.extend(
        (live_data or {}).get("data") or (live_data or {}).get("matches") or []
    )
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

    return jsonify(
        {
            "query": q,
            "players": matched_players[:limit],
            "teams": matched_teams[:limit],
            "venues": matched_venues[:limit],
            "matches": matched_matches[:limit],
        }
    )
