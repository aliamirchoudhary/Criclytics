"""Teams Venues API contracts."""

from flask import current_app, jsonify, request
from ..services.legacy import (
    load_processed,
    normalize_name,
)


from .blueprint import bp


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
    team_name, identity_id = current_app.extensions["identity_registry"].source_name(
        "team", team_name
    )
    fmt_stats = load_processed("team_format_stats.json") or {}
    venue_stats = load_processed("team_venue_stats.json") or {}
    h2h = load_processed("h2h.json") or {}

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
            is_team_a = t_a == team_name
            if opponent not in team_h2h:
                team_h2h[opponent] = {}
            team_h2h[opponent][fmt] = {
                "matches": record["matches"],
                "won": record["team_a_wins"] if is_team_a else record["team_b_wins"],
                "lost": record["team_b_wins"] if is_team_a else record["team_a_wins"],
                "tied": record["ties"],
                "drawn": record.get("draws"),
                "no_result": record["no_result"],
                "win_pct": record["team_a_win_pct"]
                if is_team_a
                else record["team_b_win_pct"],
                "last_result": record["last_result"],
            }

    return jsonify(
        {
            **({"identity_id": identity_id} if identity_id else {}),
            "name": team_name,
            "format_stats": team_data,
            "venue_stats": venue_stats.get(team_name, {}),
            "head_to_head": team_h2h,
        }
    )


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
    venue_name, identity_id = current_app.extensions["identity_registry"].source_name(
        "venue", venue_name
    )
    stats = load_processed("venue_stats.json") or {}
    batters = load_processed("venue_batters.json") or {}
    bowlers = load_processed("venue_bowlers.json") or {}

    venue = stats.get(venue_name)
    if not venue:
        candidates = [
            name for name in stats if normalize_name(name) == normalize_name(venue_name)
        ]
        if len(candidates) > 1:
            from werkzeug.exceptions import Conflict

            raise Conflict("Ambiguous venue name; use a stable identity identifier")
        if candidates:
            venue_name = candidates[0]
            venue = stats[venue_name]

    if not venue:
        # Soft-miss response to avoid noisy frontend 404s for optional context lookups.
        return jsonify(
            {"error": f"Venue '{venue_name}' not found", "found": False}
        ), 200

    if identity_id:
        venue["identity_id"] = identity_id
    venue["top_batters"] = batters.get(venue_name, [])
    venue["top_bowlers"] = bowlers.get(venue_name, [])
    store = current_app.extensions["player_id_store"]
    if store:
        venue["top_batters"] = store.document("venue:batters:" + venue_name) or []
        venue["top_bowlers"] = store.document("venue:bowlers:" + venue_name) or []
        venue["player_leaderboard_scope"] = "Observed matches across formats"

    return jsonify(venue)


@bp.route("/api/team-venue-stats")
def get_team_venue_stats():
    """All teams' venue-wise records by format."""
    data = load_processed("team_venue_stats.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500
    return jsonify(data)


@bp.route("/api/h2h")
def get_h2h():
    """
    Head-to-head between two teams.
    Query params: team_a, team_b, format (optional)
    """
    team_a = request.args.get("team_a", "")
    team_b = request.args.get("team_b", "")
    fmt = request.args.get("format")
    if fmt == "T20":
        fmt = "T20I"

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
                oriented["team_a"], oriented["team_b"] = team_a, team_b
                if team_a != ka:
                    for left, right in (
                        ("team_a_wins", "team_b_wins"),
                        ("team_a_win_pct", "team_b_win_pct"),
                    ):
                        oriented[left], oriented[right] = (
                            record.get(right),
                            record.get(left),
                        )
                results[kf] = oriented

    if not results:
        # Soft-miss response for optional sidebar context.
        return jsonify(
            {"error": f"No H2H data found for {team_a} vs {team_b}", "found": False}
        ), 200

    return jsonify(results[fmt] if fmt else results)
