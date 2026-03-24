"""
PASTE THESE ROUTES INTO app.py
================================
Add these after your existing routes, before the if __name__ == "__main__" block.
Also add this import at the top of app.py:

    from scrape_rankings import get_current_rankings

And add STATIC_DIR path near the top:

    STATIC_DIR = os.path.join(BASE_DIR, "data", "static")
"""

# ── Add this near the top of app.py (after LIVE_DIR line) ────────────────────
# STATIC_DIR = os.path.join(BASE_DIR, "data", "static")


# ── ICC Rankings endpoint ─────────────────────────────────────────────────────

# @app.route("/api/icc-rankings")
# def get_icc_rankings():
#     """
#     Official ICC rankings scraped from icc-cricket.com.
#     Cached for 24 hours. Scrapes fresh if cache is stale.
#     Query params:
#         category — batting / bowling / allrounder / teams (default: batting)
#         format   — Test / ODI / T20I (default: T20I)
#     """
#     from scrape_rankings import get_current_rankings
#
#     category = request.args.get("category", "batting")
#     fmt      = request.args.get("format", "T20I")
#
#     data = get_current_rankings()
#     if not data:
#         return jsonify({"error": "Could not fetch rankings"}), 500
#
#     if category == "teams":
#         result = data.get("team", {}).get(fmt, [])
#     else:
#         result = data.get("player", {}).get(category, {}).get(fmt, [])
#
#     return jsonify({
#         "category":   category,
#         "format":     fmt,
#         "scraped_at": data.get("scraped_at"),
#         "rankings":   result,
#     })


# ── Static metadata endpoints ─────────────────────────────────────────────────

# @app.route("/api/meta/players")
# def get_players_meta():
#     """Static player metadata — DOB, birthplace, cap numbers, photo URLs."""
#     path = os.path.join(STATIC_DIR, "players_meta.json")
#     if not os.path.exists(path):
#         return jsonify({"error": "players_meta.json not found — run create_static_files.py"}), 500
#     with open(path, encoding="utf-8") as f:
#         return jsonify(json.load(f))


# @app.route("/api/meta/players/<player_name>")
# def get_player_meta(player_name):
#     """Static metadata for one player."""
#     path = os.path.join(STATIC_DIR, "players_meta.json")
#     if not os.path.exists(path):
#         return jsonify({"error": "players_meta.json not found"}), 500
#     with open(path, encoding="utf-8") as f:
#         data = json.load(f)
#     meta = data.get(player_name)
#     if not meta:
#         # Try partial match
#         name_lower = player_name.lower()
#         for key, val in data.items():
#             if name_lower in key.lower() or name_lower in val.get("full_name","").lower():
#                 return jsonify(val)
#         return jsonify({"error": f"No meta for '{player_name}'"}), 404
#     return jsonify(meta)


# @app.route("/api/meta/teams")
# def get_teams_meta():
#     """Static team metadata — board, founded, WC titles, confederation."""
#     path = os.path.join(STATIC_DIR, "teams_meta.json")
#     if not os.path.exists(path):
#         return jsonify({"error": "teams_meta.json not found — run create_static_files.py"}), 500
#     with open(path, encoding="utf-8") as f:
#         return jsonify(json.load(f))


# @app.route("/api/meta/venues")
# def get_venues_meta():
#     """Static venue metadata — capacity, pitch type, dew factor etc."""
#     path = os.path.join(STATIC_DIR, "venues_meta.json")
#     if not os.path.exists(path):
#         return jsonify({"error": "venues_meta.json not found — run create_static_files.py"}), 500
#     with open(path, encoding="utf-8") as f:
#         return jsonify(json.load(f))


# ── Combined player profile (Cricsheet + Static meta merged) ──────────────────

# @app.route("/api/profile/player/<player_name>")
# def get_full_player_profile(player_name):
#     """
#     Full player profile merging:
#       - Cricsheet stats (players_index.json)
#       - Static meta (players_meta.json)
#       - Year-by-year, vs opposition, at venues
#     This is the endpoint your player-profile.html page should call.
#     """
#     # Cricsheet stats
#     stats_data = load_processed("players_index.json") or {}
#     stats = stats_data.get(player_name)
#     if not stats:
#         name_lower = player_name.lower()
#         for key, val in stats_data.items():
#             if key.lower() == name_lower:
#                 stats = val
#                 player_name = key
#                 break
#
#     # Static meta
#     meta_path = os.path.join(STATIC_DIR, "players_meta.json")
#     meta = {}
#     if os.path.exists(meta_path):
#         with open(meta_path, encoding="utf-8") as f:
#             all_meta = json.load(f)
#         meta = all_meta.get(player_name, {})
#         if not meta:
#             for key, val in all_meta.items():
#                 if key.lower() == player_name.lower():
#                     meta = val
#                     break
#
#     if not stats and not meta:
#         return jsonify({"error": f"Player '{player_name}' not found"}), 404
#
#     # Merge
#     profile = {**(stats or {}), **meta}
#
#     # Add extra data
#     yearly = load_processed("player_yearly.json") or {}
#     vs_opp = load_processed("player_vs_opp.json") or {}
#     venues = load_processed("player_venues.json") or {}
#
#     profile["yearly"]    = yearly.get(player_name, {})
#     profile["vs_opp"]    = vs_opp.get(player_name, {})
#     profile["at_venues"] = venues.get(player_name, {})
#
#     return jsonify(profile)
