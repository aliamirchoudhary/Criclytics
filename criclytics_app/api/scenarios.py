"""Bounded read-only experimental scenarios; never collect data or accept model paths."""

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest

bp = Blueprint("scenarios", __name__)


@bp.get("/api/v1/scenarios/catalog")
def catalog():
    model = current_app.extensions["scenario_model"]
    return jsonify(
        model.catalog()
        if model
        else {
            "available": False,
            "experimental": True,
            "reason": "No reviewed contextual model is configured",
            "promoted": False,
            "venues": [],
            "teams": [],
        }
    )


@bp.get("/api/v1/scenarios")
def scenario():
    model = current_app.extensions["scenario_model"]
    if not model:
        return jsonify(
            {
                "available": False,
                "experimental": True,
                "promoted": False,
                "reason": "No reviewed contextual model is configured",
                "distribution": None,
            }
        )
    allowed = {
        "batter",
        "bowler",
        "venue",
        "team_a",
        "team_b",
        "innings",
        "phase",
        "as_of",
    }
    if set(request.args) - allowed:
        raise BadRequest(
            "Unsupported scenario input; hypothetical psychological assumptions are not model features"
        )
    try:
        teams = [request.args.get("team_a", ""), request.args.get("team_b", "")]
        if not any(teams):
            teams = []
        result = model.predict(
            request.args.get("batter", ""),
            request.args.get("bowler", ""),
            request.args.get("venue", ""),
            teams,
            int(request.args.get("innings", "1")),
            int(request.args.get("phase", "0")),
            request.args.get("as_of"),
        )
    except (ValueError, TypeError) as error:
        raise BadRequest(str(error)) from None
    return jsonify(result)


@bp.after_request
def no_current_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response
