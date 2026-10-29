"""Records API contracts."""

from flask import current_app, jsonify, request
from ..services.legacy import (
    load_processed,
)


from .blueprint import bp


@bp.route("/api/rankings")
def get_rankings():
    """
    Returns players ranked by a stat.
    Query params:
        format  â€” Test / ODI / T20I  (required)
        type    â€” batting / bowling   (default: batting)
        limit   â€” number of results   (default: 10)
    """
    fmt = request.args.get("format", "T20I")
    rtype = request.args.get("type", "batting")
    limit = int(request.args.get("limit", 10))

    store = current_app.extensions["player_id_store"]
    if store:
        return jsonify(
            {
                "format": fmt,
                "type": rtype,
                "results": store.rankings(fmt, rtype, limit),
                "identity_correct": True,
            }
        )

    data = load_processed("players_index.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    results = []
    for name, player in data.items():
        if rtype == "batting":
            stats = player.get("batting", {}).get(fmt)
            if stats and stats.get("innings", 0) >= 5:
                results.append(
                    {
                        "player": name,
                        "matches": stats["matches"],
                        "innings": stats["innings"],
                        "runs": stats["runs"],
                        "average": stats["average"],
                        "strike_rate": stats["strike_rate"],
                        "hundreds": stats["hundreds"],
                        "fifties": stats["fifties"],
                        "highest": stats["highest"],
                    }
                )
        else:  # bowling
            stats = player.get("bowling", {}).get(fmt)
            if stats and stats.get("wickets", 0) >= 5:
                results.append(
                    {
                        "player": name,
                        "matches": stats["matches"],
                        "wickets": stats["wickets"],
                        "average": stats["average"],
                        "economy": stats["economy"],
                        "five_wkts": stats["five_wkts"],
                    }
                )

    sort_key = "runs" if rtype == "batting" else "wickets"
    results.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    return jsonify(
        {
            "format": fmt,
            "type": rtype,
            "results": results[:limit],
        }
    )


@bp.route("/api/records")
def get_records():
    """All-time records, enriched with country from players_index."""
    store = current_app.extensions["player_id_store"]
    if store:
        return jsonify({**store.records(), "sidebar": {}, "identity_correct": True})
    data = load_processed("records.json")
    if data is None:
        return jsonify({"error": "Data not found"}), 500

    # Enrich each player entry with their country from players_index
    players_index = load_processed("players_index.json") or {}
    country_map = {
        name: info.get("country", "") for name, info in players_index.items()
    }

    def enrich_list(lst):
        for entry in lst or []:
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

    provided_sidebar = (
        data.get("sidebar") if isinstance(data.get("sidebar"), dict) else {}
    )

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
            rows = (data.get(cat) or {}).get(fmt) or []
            if not rows:
                continue
            top = sorted(rows, key=lambda e: _num(e, metric), reverse=True)[0]
            sidebar["all_time_bests"].append(
                {
                    "name": top.get("player") or top.get("name") or "",
                    "country": top.get("country", ""),
                    "label": label,
                    "value": top.get(metric),
                    "type": "player",
                }
            )

    # 2) Records by Country: prefer provided payload, else count enriched top-list entries.
    by_country = provided_sidebar.get("records_by_country")
    if isinstance(by_country, list) and by_country:
        sidebar["records_by_country"] = by_country
    else:
        counts = {}
        for cat in ("most_runs", "most_wickets", "best_averages", "most_hundreds"):
            by_fmt = data.get(cat) or {}
            for fmt in ("Test", "ODI", "T20I"):
                for entry in by_fmt.get(fmt) or []:
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
    top_venues = sorted(
        venue_stats.keys(), key=lambda v: venue_stats[v].get("matches", 0), reverse=True
    )[:5]

    return jsonify({v: data[v] for v in top_venues if v in data})
