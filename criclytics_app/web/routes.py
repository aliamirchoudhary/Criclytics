"""Public pages are an explicit allowlist; private files are never served."""
from flask import Blueprint, abort, current_app, make_response, redirect, request, send_from_directory, url_for

from ..frontend import runtime_script

bp = Blueprint("web", __name__)
PAGES = frozenset({
    "index.html", "about.html", "compare.html", "data-sources.html", "disclaimer.html",
    "matches.html", "match-detail.html", "match-upcoming.html", "players.html",
    "player-profile.html", "teams.html", "team-profile.html", "venues.html",
    "venue-profile.html", "rankings.html", "records.html", "search.html", "workspace.html", "scouting.html",
})


@bp.get("/")
def index():
    return page("index.html")


@bp.get("/<path:filename>")
def page(filename):
    if filename not in PAGES:
        from pathlib import Path
        for category in ("js", "css", "images"):
            if "/" not in filename and (Path(current_app.static_folder) / category / filename).is_file():
                return redirect(url_for("static", filename=category + "/" + filename), code=308)
        abort(404)
    return send_from_directory(current_app.template_folder, filename)


@bp.get("/static/js/runtime-config.js")
def frontend_config():
    response = make_response(runtime_script(current_app.config["FRONTEND_API_BASE"]))
    response.mimetype = "application/javascript"
    response.headers["Cache-Control"] = "no-store"
    return response
