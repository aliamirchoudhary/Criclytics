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

from ..paths import PROJECT_ROOT
import json
import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")  # Load .env file so CRICAPI_KEY is available

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = str(PROJECT_ROOT)
LIVE_DIR   = os.path.join(BASE_DIR, "data", "live")
os.makedirs(LIVE_DIR, exist_ok=True)

# Read key from app.py automatically so you only set it in one place
def get_api_key():
    return os.environ.get("CRICAPI_KEY", "")

CRICAPI_KEY  = get_api_key()  # Use the helper function to read from app.py first, then .env
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
    from .source_policy import require_source
    require_source('cricapi')
    if not CRICAPI_KEY:
        print("  ✗  No CricAPI key found.")
        return None

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
                print("Provider returned an error response")
                return None
            return data

        except requests.exceptions.Timeout:
            print(f"  ✗  Timeout on /{endpoint} — network is blocking CricAPI")
            return None  # Don't retry timeouts — it's a network block
        except requests.exceptions.RequestException as e:
            print("Provider request failed type=" + type(e).__name__)
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
        matches = data.get("data") or data.get("matches") or []
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
    data = cricapi_get("match_info", params={"id": unique_id})
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
    data = cricapi_get("match_scorecard", params={"id": unique_id})
    if data:
        save(f"score_{unique_id}.json", data)
        return data
    return None


def fetch_player_photo(player_name):
    raise RuntimeError("Legacy photo fetching is retired; use the reviewed media manifest workflow")


def fetch_photos_for_players(player_names):
    raise RuntimeError("Legacy photo fetching is retired; use the reviewed media manifest workflow")


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

    print("CricAPI credential configured; value withheld")
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
