"""
fetch_live.py
=============
Cricklytics — CricAPI Live Data Fetcher (Source A)
Fetches live scores, upcoming fixtures, series info and match details.
Run this on a schedule or call individual functions from app.py.

Usage:
    python fetch_live.py              # fetch everything once
    python fetch_live.py --live       # only live scores
    python fetch_live.py --fixtures   # only fixtures
    python fetch_live.py --series     # only series
"""

import json
import os
import sys
import time
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LIVE_DIR   = os.path.join(BASE_DIR, "data", "live")
os.makedirs(LIVE_DIR, exist_ok=True)

# Read key from app.py automatically so you only set it in one place
def get_api_key():
    app_path = os.path.join(BASE_DIR, "app.py")
    try:
        with open(app_path) as f:
            for line in f:
                if "CRICAPI_KEY" in line and "=" in line and "#" not in line.split("=")[0]:
                    key = line.split("=")[1].strip().strip('"').strip("'")
                    if key and key != "YOUR_CRICAPI_KEY_HERE":
                        return key
    except Exception:
        pass
    return os.environ.get("CRICAPI_KEY", "")

CRICAPI_KEY  = "f6413cdc-8355-433a-823a-f3dd4a254f3f"
CRICAPI_BASE = "https://api.cricapi.com/v1"

# ── Helpers ───────────────────────────────────────────────────────────────────
def save(filename, data):
    path = os.path.join(LIVE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "data": data
        }, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(path) / 1024
    print(f"  ✓  {filename:<30} {size:>7.1f} KB  [{datetime.now().strftime('%H:%M:%S')}]")


def cricapi_get(endpoint, params=None, retries=2):
    """Make a CricAPI request. Fails fast if network is blocked."""
    if not CRICAPI_KEY:
        print("  ✗  No CricAPI key found.")
        return None

    # Quick reachability check first (1 second timeout to DNS)
    import socket
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("api.cricapi.com", 443))
    except (socket.timeout, OSError):
        print(f"  ✗  api.cricapi.com is not reachable from this network (blocked/offline)")
        print(f"     Skipping all CricAPI calls. Use a VPN or different network.")
        return None
    finally:
        socket.setdefaulttimeout(None)

    p = {"apikey": CRICAPI_KEY, "offset": 0}
    if params:
        p.update(params)

    for attempt in range(retries):
        try:
            resp = requests.get(
                f"{CRICAPI_BASE}/{endpoint}",
                params=p,
                timeout=8
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                print(f"  ✗  CricAPI error on /{endpoint}: {data['error']}")
                return None
            return data

        except requests.exceptions.Timeout:
            print(f"  ✗  Timeout on /{endpoint} — network is blocking CricAPI")
            return None  # Don't retry timeouts — it's a network block
        except requests.exceptions.RequestException as e:
            print(f"  ✗  Request failed on /{endpoint}: {e}")
            return None

    return None


# ── Fetchers ──────────────────────────────────────────────────────────────────

def fetch_live_matches():
    """
    Fetch all currently live matches.
    Saves: data/live/live.json
    Cost: 1 req — call hourly
    """
    print("Fetching live matches …")
    data = cricapi_get("currentMatches")
    if data:
        matches = data.get("matches", [])
        print(f"  Found {len(matches)} live match(es)")
        save("live.json", matches)
        return matches
    return []


def fetch_fixtures():
    """
    Fetch upcoming and recent matches.
    Saves: data/live/matches.json
    Cost: 1 req — call once daily
    """
    print("Fetching fixtures …")
    data = cricapi_get("matches")
    if data:
        matches = data.get("matches", [])
        print(f"  Found {len(matches)} match(es)")
        save("matches.json", matches)
        return matches
    return []


def fetch_series():
    """
    Fetch active series list.
    Saves: data/live/series.json
    Cost: 1 req — call once daily
    """
    print("Fetching series …")
    data = cricapi_get("series")
    if data:
        series = data.get("series_list", data.get("series", []))
        print(f"  Found {len(series)} series")
        save("series.json", series)
        return series
    return []


def fetch_match_detail(unique_id):
    """
    Fetch full detail for one match (toss, umpires, venue, etc.).
    Saves: data/live/match_{unique_id}.json
    Cost: 1 req per match — call once per match, result is permanent
    """
    print(f"Fetching match detail: {unique_id} …")
    data = cricapi_get("match_info", params={"unique_id": unique_id})
    if data:
        save(f"match_{unique_id}.json", data)
        return data
    return None


def fetch_match_scorecard(unique_id):
    """
    Fetch live scorecard for a match.
    Saves: data/live/score_{unique_id}.json
    Cost: 1 req — call hourly for live matches
    """
    print(f"Fetching scorecard: {unique_id} …")
    data = cricapi_get("match_scorecard", params={"unique_id": unique_id})
    if data:
        save(f"score_{unique_id}.json", data)
        return data
    return None


def fetch_player_photo(player_name):
    """
    Fetch photo URL for a player.
    Saves: appends to data/static/players_meta.json
    Cost: 1 req per player — call once, cached permanently
    Note: First searches for the player, then fetches their stats for imageURL.
    """
    print(f"Fetching photo for: {player_name} …")

    # Step 1: find the player's CricAPI ID
    search_data = cricapi_get("players", params={"namePart": player_name})
    if not search_data:
        return None

    players = search_data.get("data", [])
    if not players:
        print(f"  ⚠  Player '{player_name}' not found in CricAPI")
        return None

    # Take the first result
    player_id = players[0].get("pid") or players[0].get("unique_id")
    if not player_id:
        return None

    # Step 2: fetch player stats (contains imageURL)
    stats_data = cricapi_get("players_info", params={"pid": player_id})
    if not stats_data:
        return None

    image_url = stats_data.get("imageURL", "")
    print(f"  ✓  Photo URL: {image_url[:60]}…" if image_url else "  ⚠  No photo URL")

    return {
        "pid":       player_id,
        "image_url": image_url,
        "name":      stats_data.get("name", player_name),
    }


def fetch_photos_for_players(player_names):
    """
    Bulk fetch photo URLs for a list of players.
    Updates data/static/players_meta.json with image URLs.
    Cost: 2 req per player (search + stats) — run once during setup.
    Tip: Only fetch for ~50 featured players, not all 3800.
    """
    meta_path = os.path.join(BASE_DIR, "data", "static", "players_meta.json")
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)

    # Load existing meta
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    else:
        meta = {}

    print(f"\nFetching photos for {len(player_names)} players …")
    print("(2 API requests per player — spread over multiple days if needed)\n")

    for name in player_names:
        if meta.get(name, {}).get("image_url"):
            print(f"  ↷  {name} — already cached, skipping")
            continue

        result = fetch_player_photo(name)
        if result:
            if name not in meta:
                meta[name] = {}
            meta[name]["image_url"] = result["image_url"]
            meta[name]["cricapi_pid"] = result["pid"]

        # Save after each player in case script is interrupted
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # Be polite to the API
        time.sleep(1)

    print(f"\n  ✓  Updated {meta_path}")
    return meta


def fetch_squad(series_id):
    """
    Fetch squad for a series.
    Saves: data/live/squad_{series_id}.json
    Cost: 1 req — call once per new series
    """
    print(f"Fetching squad for series: {series_id} …")
    data = cricapi_get("series_squad", params={"unique_id": series_id})
    if data:
        save(f"squad_{series_id}.json", data)
        return data
    return None


# ── Daily budget summary ──────────────────────────────────────────────────────

def fetch_all_daily():
    """
    Fetch everything needed for a normal day.
    Will immediately detect if CricAPI is network-blocked and exit cleanly.
    """
    print("=" * 55)
    print("  Cricklytics — Daily CricAPI Fetch")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    result = fetch_live_matches()
    if result is None and not isinstance(result, list):
        print("\n  ✗  Network blocked — CricAPI unreachable.")
        print("  Solutions:")
        print("    1. Enable a VPN and re-run this script")
        print("    2. Use mobile hotspot instead of current network")
        print("    3. Try from a different network")
        print("\n  The app will use cached data from data/live/ if available.")
        print("=" * 55)
        return

    fetch_fixtures()
    fetch_series()

    print("\n  Daily fetch complete.")
    print("=" * 55)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not CRICAPI_KEY:
        print("✗  CricAPI key not found. Set CRICAPI_KEY in app.py first.")
        sys.exit(1)

    print(f"  CricAPI key: {CRICAPI_KEY[:8]}…")
    print()

    if "--live" in args:
        fetch_live_matches()
    elif "--fixtures" in args:
        fetch_fixtures()
    elif "--series" in args:
        fetch_series()
    elif "--photos" in args:
        # Fetch photos for featured players
        # Add or remove names as needed
        featured = [
            "V Kohli", "RG Sharma", "JJ Bumrah", "HH Pandya",
            "R Jadeja", "KL Rahul", "SPD Smith", "DA Warner",
            "PJ Cummins", "MG Johnson", "JE Root", "BA Stokes",
            "Babar Azam", "Shaheen Afridi", "Kane Williamson",
            "TG Southee", "K Rabada", "Q de Kock",
        ]
        fetch_photos_for_players(featured)
    else:
        fetch_all_daily()
