"""Bounded inputs and redacted API errors, independent of dataset availability."""

import re
import uuid

from flask import g, jsonify, request
from werkzeug.exceptions import BadRequest, HTTPException, UnsupportedMediaType

FORMATS = {"Test", "ODI", "T20I", "T20"}
METRICS = {"50", "100", "wicket_maiden", "strike_rate>140", "avg>50"}


def text(value, field, required=False, maximum=200):
    if (
        not isinstance(value, str)
        or len(value) > maximum
        or re.search(r"[\x00-\x1f\x7f]", value)
    ):
        raise BadRequest(field + " must be bounded plain text")
    if required and not value.strip():
        raise BadRequest(field + " is required")
    return value.strip()


def error_response(status, message, code=None):
    return jsonify(
        error=message,
        code=code or "HTTP_" + str(status),
        request_id=getattr(g, "request_id", uuid.uuid4().hex),
    ), status


def register(app):
    @app.before_request
    def validate_api_request():
        if not request.path.startswith("/api/"):
            return
        g.request_id = uuid.uuid4().hex
        if len(request.query_string) > 4096 or len(request.args) > 20:
            raise BadRequest("Query exceeds the bounded public request size")
        for field, values in request.args.lists():
            text(field, "query field", required=True, maximum=64)
            if len(values) != 1:
                raise BadRequest("Duplicate query parameter: " + field)
            value = text(values[0], field)
            if field in {"limit", "offset", "page", "page_size"}:
                if not re.fullmatch(r"[0-9]{1,6}", value):
                    raise BadRequest(field + " must be a bounded integer")
                upper = (
                    100000 if field == "offset" else 10000 if field == "page" else 500
                )
                lower = 0 if field == "offset" else 1
                if not lower <= int(value) <= upper:
                    raise BadRequest(field + " is outside the allowed range")
            if field == "format" and value not in FORMATS:
                raise BadRequest("Unsupported format")
            if field == "metric" and value not in METRICS:
                raise BadRequest("Unsupported metric")
        for field, value in (request.view_args or {}).items():
            if isinstance(value, str):
                text(value, field, required=True)
                if field == "match_id" and not re.fullmatch(
                    r"[A-Za-z0-9_-]{1,100}", value
                ):
                    raise BadRequest("Invalid match identifier")
        if request.path == "/api/predict/team_match" and request.method == "POST":
            if not request.is_json:
                raise UnsupportedMediaType("Use application/json")
            data = request.get_json()
            if not isinstance(data, dict):
                raise BadRequest("Request body must be a JSON object")
            for field in ("team_a", "team_b"):
                data[field] = text(data.get(field), field, required=True)
            if data["team_a"].casefold() == data["team_b"].casefold():
                raise BadRequest("Choose two different teams")
            if (
                not isinstance(data.get("format", "ODI"), str)
                or data.get("format", "ODI") not in FORMATS
            ):
                raise BadRequest("Unsupported format")
            if data.get("venue") is not None:
                text(data["venue"], "venue")

    @app.errorhandler(Exception)
    def handle_error(exc):
        if isinstance(exc, HTTPException):
            if not request.path.startswith("/api/"):
                return exc
            return error_response(
                exc.code or 500,
                exc.description
                if exc.code and exc.code < 500
                else "Internal server error",
            )
        app.logger.error(
            "Unhandled request failure type=%s request_id=%s",
            type(exc).__name__,
            getattr(g, "request_id", "unknown"),
        )
        return error_response(500, "Internal server error")

    @app.after_request
    def normalize_api_error(response):
        if not request.path.startswith("/api/"):
            return response
        response.headers["X-Request-ID"] = getattr(g, "request_id", uuid.uuid4().hex)
        payload = response.get_json(silent=True)
        if isinstance(payload, dict) and "error" in payload:
            status = response.status_code
            if payload.get("found") is False:
                status = 404
            elif status < 400:
                status = 400
            if status >= 500:
                unavailable = any(
                    word in str(payload.get("error", "")).lower()
                    for word in (
                        "not found",
                        ".json",
                        "not initialized",
                        "create_static",
                    )
                )
                status = 503 if unavailable else status
                message = (
                    "Required data or service is unavailable"
                    if status == 503
                    else "Internal server error"
                )
            else:
                message = str(payload["error"])
            payload = {
                "error": message,
                "code": "HTTP_" + str(status),
                "request_id": getattr(g, "request_id", "unknown"),
            }
            response.set_data(app.json.dumps(payload))
            response.status_code = status
        return response
