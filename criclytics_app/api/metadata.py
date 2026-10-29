"""Metadata API contracts."""

import json
import os
import sqlite3
from flask import current_app, jsonify, request
from ..services.legacy import (
    PROCESSED_DIR,
    STATIC_DIR,
)


from .blueprint import bp


@bp.get("/api/health")
def health():
    return jsonify({"status": "alive"})


@bp.get("/api/ready")
@bp.get("/api/status")
def status():
    from ..services.diagnostics import readiness

    data = readiness(current_app)
    return jsonify(data), 200 if data["ready"] else 503


@bp.route("/api/icc-rankings")
def get_icc_rankings():
    category = request.args.get("category", "batting")
    fmt = request.args.get("format", "T20I")
    from werkzeug.exceptions import BadRequest
    from ..services.provenance import metadata

    if category not in ("teams", "batting", "bowling", "allrounder"):
        raise BadRequest("Unsupported ranking category")
    from ..integrations.ranking_snapshots import read
    from ..web.local_access import is_local_request

    store = current_app.config["RANKING_SNAPSHOT_STORE"]
    # Personal extracts cannot become a public feed through a config switch.
    data = None
    if store and is_local_request():
        try:
            data = read(store, category, fmt)
        except (OSError, ValueError, KeyError, sqlite3.Error):
            pass
    info = metadata(data)
    response = jsonify(
        {
            "available": data is not None,
            "category": category,
            "format": fmt,
            "rankings": data["rankings"] if data else [],
            "provenance": info,
            **info,
            "source_url": data["source_url"]
            if data
            else "https://www.icc-cricket.com/rankings",
            "rights_scope": "local_personal_only"
            if data
            else "no_approved_public_snapshot",
            "backup_used": data.get("backup_used", False) if data else False,
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return response


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
            if (
                player_name.lower() in key.lower()
                or player_name.lower() in val.get("full_name", "").lower()
            ):
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


@bp.get("/api/coverage")
def dataset_coverage():
    from ..services.repository import safe_file

    coverage = current_app.extensions["json_repository"].read(
        safe_file(PROCESSED_DIR, "coverage.json")
    )
    if not coverage:
        return jsonify(
            {
                "available": False,
                "dataset_id": None,
                "data_cutoff": None,
                "scope": "Legacy historical subset; exact coverage metadata unavailable",
            }
        )
    manifest = (
        current_app.extensions["json_repository"].read(
            safe_file(PROCESSED_DIR, "manifest.json")
        )
        or {}
    )
    return jsonify(
        {"available": True, "dataset_id": manifest.get("dataset_id"), **coverage}
    )


@bp.get("/api/identities/<kind>/<identifier>")
def identity_record(kind, identifier):
    from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable

    if kind not in ("player", "team", "venue", "match"):
        raise BadRequest("Unsupported identity kind")
    registry = current_app.extensions["identity_registry"]
    if not registry.data:
        raise ServiceUnavailable("Identity registry unavailable for this dataset")
    item = registry.resolve(kind, identifier)
    if not item:
        raise NotFound("Identity not found")
    return jsonify({"dataset_id": registry.data["dataset_id"], "identity": item})
