"""Public pages are an explicit allowlist; private files are never served."""
from flask import Blueprint, abort, current_app, make_response, redirect, request, send_from_directory, url_for

from ..services.legacy import render_match_detail_bootstrap, resolve_match_detail

bp = Blueprint("web", __name__)
PAGES = frozenset({
    "index.html", "about.html", "compare.html", "data-sources.html", "disclaimer.html",
    "matches.html", "match-detail.html", "match-upcoming.html", "players.html",
    "player-profile.html", "teams.html", "team-profile.html", "venues.html",
    "venue-profile.html", "rankings.html", "records.html", "search.html",
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
    if filename == "match-detail.html":
        from pathlib import Path
        html = (Path(current_app.template_folder) / filename).read_text(encoding="utf-8")
        match_id = request.args.get("id", "").strip()
        match = resolve_match_detail(match_id) if match_id else None
        if match:
            html = html.replace("</body>", render_match_detail_bootstrap(match) + "\n</body>")
        return make_response(html)
    return send_from_directory(current_app.template_folder, filename)
