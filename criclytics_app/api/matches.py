"""Matches API contracts."""

from datetime import datetime
from flask import current_app, jsonify, request
from ..services.legacy import (
    LIVE_CACHE_TTL_MINUTES,
    MATCH_INFO_CACHE_TTL_MINUTES,
    MATCH_LIST_CACHE_TTL_MINUTES,
    SCORECARD_CACHE_TTL_MINUTES,
    SERIES_CACHE_TTL_MINUTES,
    augment_completed_match,
    completed_match,
    completed_summaries,
    cache_age_minutes,
    fetch_cricapi,
    load_live,
    save_live,
)


from .blueprint import bp


@bp.route("/api/live")
def get_live():
    """Live match scores. Falls back to sample cache if API returns empty."""
    data = fetch_cricapi(
        "currentMatches", cache_file="live.json", max_age_minutes=LIVE_CACHE_TTL_MINUTES
    )
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
        if m.get("score") or []:
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
        cached_sc_data = (
            (cached_sc or {}).get("data") if isinstance(cached_sc, dict) else None
        )
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
            save_live(
                daily_scorecard_gate_file,
                {
                    "last_call_at": datetime.now().isoformat(),
                    "match_id": mid,
                },
            )
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
    data = fetch_cricapi(
        "matches",
        cache_file="matches.json",
        max_age_minutes=MATCH_LIST_CACHE_TTL_MINUTES,
    )
    cached = None
    live_upcoming = (data or {}).get("data") or (data or {}).get("matches") or []
    if not live_upcoming:
        cached = load_live("matches.json")
        live_upcoming = (
            (cached or {}).get("data") or (cached or {}).get("matches") or []
        )

    # Get completed matches from Cricsheet
    completed = completed_summaries()

    from criclytics_app.services.match_listing import listing
    from ..services.provenance import metadata

    result = listing(
        live_upcoming,
        completed,
        request.args,
        current_app.extensions["identity_registry"],
    )
    result["provenance"] = metadata(data or cached)
    result["provenance"]["historical_source"] = "cricsheet_legacy_processed"
    return jsonify(result)


@bp.route("/api/matches/<match_id>")
def get_match(match_id):
    """Individual match detail. Searches live/upcoming and completed matches."""
    match = completed_match(match_id)
    if match:
        return jsonify({"data": augment_completed_match(match)})

    cache_file = f"match_{match_id}.json"
    data = fetch_cricapi(
        "match_info",
        params={"id": match_id},
        cache_file=cache_file,
        max_age_minutes=MATCH_INFO_CACHE_TTL_MINUTES,
    )
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
        return jsonify({"data": augment_completed_match(match)})

    cache_file = f"score_{match_id}.json"
    data = fetch_cricapi(
        "match_scorecard",
        params={"id": match_id},
        cache_file=cache_file,
        max_age_minutes=SCORECARD_CACHE_TTL_MINUTES,
    )
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
    data = fetch_cricapi(
        "series", cache_file="series.json", max_age_minutes=SERIES_CACHE_TTL_MINUTES
    )
    if data:
        series = data.get("data") or data.get("series") or data.get("series_list") or []
        return jsonify({"data": series})
    cached = load_live("series.json")
    if cached:
        series = (
            cached.get("data")
            or cached.get("series")
            or cached.get("series_list")
            or []
        )
        return jsonify({"data": series, "cached": True})
    return jsonify({"data": [], "note": "No series data available"})
