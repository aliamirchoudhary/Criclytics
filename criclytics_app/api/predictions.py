"""Predictions API contracts."""

from flask import jsonify, request


from .blueprint import bp


def unavailable_prediction(**context):
    from ..ml.probability import unavailable

    return jsonify(unavailable(**context))


@bp.route("/api/predict/player/<player_name>")
def predict_player(player_name):
    return unavailable_prediction(
        player=player_name,
        metric=request.args.get("metric", "50"),
        format=request.args.get("format", "ODI"),
    )


@bp.route("/api/predict/player/<player_name>/all")
def predict_player_all(player_name):
    return unavailable_prediction(
        player=player_name, format=request.args.get("format", "ODI"), predictions={}
    )


@bp.route("/api/predict/team_match", methods=["POST"])
def predict_team_match():
    data = request.get_json()
    return unavailable_prediction(
        team_a=data["team_a"], team_b=data["team_b"], format=data.get("format", "ODI")
    )


@bp.route("/api/predict/venue/<venue_name>")
def predict_venue(venue_name):
    return unavailable_prediction(
        venue=venue_name, format=request.args.get("format", "ODI")
    )


@bp.route("/api/predict/leaderboard")
def predict_leaderboard():
    return unavailable_prediction(
        predictions=[],
        evaluated_players=0,
        metric=request.args.get("metric", "50"),
        format=request.args.get("format", "ODI"),
    )


@bp.route("/api/predict/status")
def predict_status():
    return unavailable_prediction(engine_active=False)
