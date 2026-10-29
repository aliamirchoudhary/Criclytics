"""Compatibility CLI and aggregation helpers.

Run: python -m criclytics_app.pipeline.cricsheet --output <fresh-private-candidate>
Delegates to the validated non-overwriting rebuild. Scoring/aggregation own cricket
semantics; summaries.py owns output projections. Original artifacts stay intact.
"""
from ..paths import PROJECT_ROOT
import json
import os
import glob
from collections import defaultdict
from datetime import datetime, date
from tqdm import tqdm

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = str(PROJECT_ROOT)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR = os.path.join(BASE_DIR, "data", "processed")


FORMAT_DIRS = {
    "Test": os.path.join(RAW_DIR, "tests_male_json"),
    "ODI": os.path.join(RAW_DIR, "odis_male_json"),
    "T20I": os.path.join(RAW_DIR, "t20s_male_json"),
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def save(filename, data):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✓  {filename:<35} {size_kb:>8.1f} KB")


def load_all_matches():
    """Load every match JSON file across all three formats."""
    matches = []
    for fmt, folder in FORMAT_DIRS.items():
        if not os.path.isdir(folder):
            print(f"  ⚠  Folder not found: {folder} — skipping {fmt}")
            continue
        files = glob.glob(os.path.join(folder, "*.json"))
        print(f"  Loading {len(files):>5} {fmt} files …")
        for filepath in tqdm(files, desc=f"  {fmt}", leave=False):
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)
                data["_format"] = fmt
                data["_file"] = os.path.basename(filepath)
                matches.append(data)
            except Exception as e:
                print(f"    ⚠  Skipping {filepath}: {e}")
    print(f"  Total matches loaded: {len(matches)}")
    return matches


def get_info(match):
    return match.get("info", {})


def get_date(match):
    """Return first date as a date object, or None."""
    dates = get_info(match).get("dates", [])
    if not dates:
        return None
    try:
        return datetime.strptime(dates[0], "%Y-%m-%d").date()
    except Exception:
        return None


def get_season(match):
    d = get_date(match)
    return d.year if d else None


def is_recent(match, years=5):
    d = get_date(match)
    if not d:
        return False
    cutoff = date.today().replace(year=date.today().year - years)
    return d >= cutoff


def get_venue(match):
    return get_info(match).get("venue", "Unknown Venue")


def get_teams(match):
    return get_info(match).get("teams", [])


def get_outcome(match):
    return get_info(match).get("outcome", {})


def get_winner(match):
    return get_outcome(match).get("winner")


def get_toss(match):
    return get_info(match).get("toss", {})


def format_toss_text(toss):
    if not isinstance(toss, dict):
        return ""
    winner = str(toss.get("winner") or "").strip()
    decision = str(toss.get("decision") or "").strip().lower()
    if winner and decision:
        if decision == "field":
            decision = "bowl"
        return f"{winner} won the toss and chose to {decision}"
    return winner or str(toss.get("decision") or "").strip()


def iter_deliveries(match):
    """
    Yields (inning_idx, over_num, delivery_dict, batting_team, bowling_team)
    for every delivery in a match.
    """
    teams = get_teams(match)
    innings = match.get("innings", [])
    for i, inning in enumerate(innings):
        batting_team = inning.get("team", "")
        bowling_team = next((t for t in teams if t != batting_team), "")
        for over in inning.get("overs", []):
            over_num = over.get("over", 0)
            for delivery in over.get("deliveries", []):
                yield i, over_num, delivery, batting_team, bowling_team


def is_wide_or_noball(delivery):
    extras = delivery.get("extras", {})
    return "wides" in extras or "noballs" in extras


def dismissal_kind(delivery):
    wickets = delivery.get("wickets", [])
    if wickets:
        return wickets[0].get("kind", "")
    return None


def dismissal_text(delivery, bowler):
    """Build 'c Warner b Starc' style string."""
    wickets = delivery.get("wickets", [])
    if not wickets:
        return ""
    w = wickets[0]
    kind = w.get("kind", "")
    fielders = [f.get("name", "") for f in w.get("fielders", [])]
    if kind == "caught":
        fielder = fielders[0] if fielders else ""
        return f"c {fielder} b {bowler}"
    elif kind == "bowled":
        return f"b {bowler}"
    elif kind in ("lbw", "hit wicket"):
        return f"{kind} b {bowler}"
    elif kind == "run out":
        fielder = fielders[0] if fielders else ""
        return f"run out ({fielder})"
    elif kind == "stumped":
        fielder = fielders[0] if fielders else ""
        return f"st {fielder} b {bowler}"
    else:
        return kind


def build_mega_enriched_view(match):
    from .scoring import score_match

    return match.get("_scored") or score_match(match)


def build_completed_matches(matches):
    """
    Extract all completed matches from Cricsheet data.
    Returns a list of match summaries formatted for frontend consumption.
    """
    print("\n[2.5/4] Extracting completed matches …")

    completed = []
    for match in tqdm(matches, desc="  Extracting", leave=False):
        info = get_info(match)
        outcome = get_outcome(match)

        # Skip if no outcome (incomplete or no result)
        if not outcome:
            continue

        # Only include if there's a winner or it's a tie
        winner = outcome.get("winner")

        teams = get_teams(match)
        if len(teams) < 2:
            continue

        match_date = get_date(match)
        if not match_date:
            continue

        # Build match record
        match_id = match.get("_file", "").replace(".json", "")
        fmt = match.get("_format") or info.get("match_type", "Unknown")
        venue = get_venue(match)
        series = info.get("event", {}).get("name", "")

        # Build status text
        by = outcome.get("by", {})
        if isinstance(by, dict):
            if "runs" in by:
                status_text = f"{winner} won by {by['runs']} runs"
            elif "wickets" in by:
                status_text = f"{winner} won by {by['wickets']} wickets"
            else:
                status_text = f"{winner} won"
        else:
            status_text = f"{winner} won"

        if not winner:
            status_text = outcome.get("result") or "no result"
        scored = build_mega_enriched_view(match)
        scores = [
            {
                "team": inn["team"],
                "r": inn["total"],
                "w": inn["wickets"],
                "o": inn["overs"],
                "inning": inn["team"] + " Innings " + str(inn["innings_id"]),
                "super_over": inn["super_over"],
            }
            for inn in scored["innings"]
        ]

        # MEGA-ENRICHMENT: Build full scorecard and officials
        officials = info.get("officials", {})
        mega_view = scored

        completed.append(
            {
                "id": match_id,
                "unique_id": match_id,
                "name": f"{teams[0]} vs {teams[1]}",
                "t1": teams[0],
                "t2": teams[1],
                "team1": teams[0],
                "team2": teams[1],
                "teams": teams,
                "type": fmt,
                "matchType": fmt,
                "format": fmt,
                "status": status_text,
                "outcome": outcome,
                "date": str(match_date),
                "dateTimeGMT": str(match_date),
                "venue": venue,
                "city": info.get("city", ""),
                "series": series,
                "series_id": series,
                "season": info.get("season"),
                "match_type_number": info.get("match_type_number"),
                "team_type": info.get("team_type"),
                "balls_per_over": info.get("balls_per_over"),
                "toss": format_toss_text(info.get("toss", {})),
                "toss_details": info.get("toss", {}),
                "officials": officials,
                "match_referee": ((officials or {}).get("match_referees") or [""])[0]
                if isinstance(officials, dict)
                else "",
                "umpires": (officials or {}).get("umpires", [])
                if isinstance(officials, dict)
                else [],
                "tv_umpires": (officials or {}).get("tv_umpires", [])
                if isinstance(officials, dict)
                else [],
                "reserve_umpires": (officials or {}).get("reserve_umpires", [])
                if isinstance(officials, dict)
                else [],
                "players": info.get("players", {}),
                "squads": info.get("players", {}),
                "score": scores,
                "innings": mega_view.get("innings", []),
                "partnerships": mega_view.get("partnerships", []),
                "match_stats": mega_view.get("match_stats", {}),
                "matchStarted": True,
                "matchEnded": True,
                "winners": [winner] if winner else [],
                "player_of_match": info.get("player_of_match", []),
            }
        )

    print(f"  Extracted {len(completed)} completed matches")
    return completed


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — BUILD RAW ACCUMULATORS
# ════════════════════════════════════════════════════════════════════════════


def build_raw_accumulators(matches):
    """
    Single pass through all deliveries building every accumulator needed.
    Returns a dict of all raw data structures.
    """
    print("\n[1/4] Building raw accumulators (single pass) …")

    # ── Player batting stats ─────────────────────────────────────────────────
    # Key: (player_name, format)
    bat = defaultdict(
        lambda: {
            "matches": set(),
            "innings": 0,
            "runs": 0,
            "balls": 0,
            "fours": 0,
            "sixes": 0,
            "fifties": 0,
            "hundreds": 0,
            "highest": 0,
            "not_outs": 0,
            "dismissals": 0,
            "innings_scores": [],  # list of scores for form
        }
    )

    # ── Player bowling stats ─────────────────────────────────────────────────
    bowl = defaultdict(
        lambda: {
            "matches": set(),
            "innings": 0,
            "balls": 0,
            "runs": 0,
            "wickets": 0,
            "maidens": 0,
            "five_wkts": 0,
            "best_wkts": 0,
            "best_runs": 999,
            "innings_wickets": [],
        }
    )

    # ── Player vs opposition (batting) ───────────────────────────────────────
    # Key: (player, format, opposition)
    bat_vs = defaultdict(
        lambda: {
            "innings": 0,
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "highest": 0,
            "hundreds": 0,
            "fifties": 0,
        }
    )

    # ── Player at venue (batting) ─────────────────────────────────────────────
    # Key: (player, format, venue)
    bat_venue = defaultdict(
        lambda: {
            "innings": 0,
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "highest": 0,
            "hundreds": 0,
            "fifties": 0,
        }
    )

    # ── Player yearly (batting) ───────────────────────────────────────────────
    # Key: (player, format, year)
    bat_year = defaultdict(
        lambda: {
            "matches": set(),
            "innings": 0,
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "hundreds": 0,
            "fifties": 0,
        }
    )

    # ── Venue scoring stats ───────────────────────────────────────────────────
    # Key: venue
    venue_data = defaultdict(
        lambda: {
            "formats": set(),
            "matches": 0,
            "innings": [],  # list of {"total", "wickets", "overs", "format", "batting_first"}
            "chase_results": [],  # list of True/False (chasing team won?)
            "toss_winner_won": 0,
            "toss_total": 0,
            "wicket_kinds": defaultdict(int),
            "powerplay_runs": [],
            "powerplay_wkts": [],
            "middle_runs": [],
            "middle_wkts": [],
            "death_runs": [],
            "death_wkts": [],
        }
    )

    # ── Team H2H ──────────────────────────────────────────────────────────────
    # Key: (team_a, team_b, format) — always sorted alphabetically
    h2h_data = defaultdict(
        lambda: {
            "matches": 0,
            "team_a_wins": 0,
            "team_b_wins": 0,
            "ties": 0,
            "draws": 0,
            "no_result": 0,
            "last_result": "",
        }
    )

    # ── Team format stats ─────────────────────────────────────────────────────
    # Key: (team, format)
    team_fmt = defaultdict(
        lambda: {
            "matches": 0,
            "won": 0,
            "lost": 0,
            "tied": 0,
            "nr": 0,
            "total_runs": 0,
            "total_innings": 0,
            "total_wkts": 0,
        }
    )

    # ── Team venue stats ──────────────────────────────────────────────────────
    # Key: (team, format, venue)
    team_venue = defaultdict(
        lambda: {
            "matches": 0,
            "won": 0,
            "lost": 0,
            "total_runs": 0,
            "innings_count": 0,
            "highest": 0,
        }
    )

    # ── Venue batter/bowler stats ─────────────────────────────────────────────
    # Key: (venue, player)
    venue_bat = defaultdict(
        lambda: {
            "matches": set(),
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "highest": 0,
            "hundreds": 0,
        }
    )
    venue_bowl = defaultdict(
        lambda: {
            "matches": set(),
            "balls": 0,
            "runs": 0,
            "wickets": 0,
            "best_wkts": 0,
            "best_runs": 999,
        }
    )

    # ── Per-match tracker ─────────────────────────────────────────────────────
    player_country = {}
    from .aggregation import aggregate

    return aggregate(matches, locals())


from .summaries import (
    avg as avg,
    sr as sr,
    econ as econ,
    bowl_avg as bowl_avg,
    build_players_index as build_players_index,
    build_player_yearly as build_player_yearly,
    build_player_vs_opp as build_player_vs_opp,
    build_player_venues as build_player_venues,
    build_h2h as build_h2h,
    build_team_format_stats as build_team_format_stats,
    build_team_venue_stats as build_team_venue_stats,
    _safe_avg as _safe_avg,
    build_venue_stats as build_venue_stats,
    build_venue_batters as build_venue_batters,
    build_venue_bowlers as build_venue_bowlers,
    build_venue_insights as build_venue_insights,
    build_records as build_records,
)


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — SAVE ALL OUTPUTS
# ════════════════════════════════════════════════════════════════════════════


def save_all(accumulators, matches):
    print("\n[4/4] Saving output files …")

    bat = accumulators["bat"]
    bowl = accumulators["bowl"]
    bat_vs = accumulators["bat_vs"]
    bat_venue = accumulators["bat_venue"]
    bat_year = accumulators["bat_year"]
    venue_data = accumulators["venue_data"]
    h2h_data = accumulators["h2h_data"]
    team_fmt = accumulators["team_fmt"]
    team_venue = accumulators["team_venue"]
    venue_bat = accumulators["venue_bat"]
    venue_bowl = accumulators["venue_bowl"]
    player_country = accumulators.get("player_country", {})

    players_index = build_players_index(bat, bowl, player_country)
    player_yearly = build_player_yearly(bat_year)
    player_vs_opp = build_player_vs_opp(bat_vs)
    player_venues = build_player_venues(bat_venue)
    h2h = build_h2h(h2h_data)
    team_format = build_team_format_stats(team_fmt)
    team_venue_out = build_team_venue_stats(team_venue)
    venue_stats = build_venue_stats(venue_data)
    venue_batters = build_venue_batters(venue_bat)
    venue_bowlers = build_venue_bowlers(venue_bowl)
    venue_insights = build_venue_insights(venue_stats)
    records = build_records(bat, bowl, matches)

    save("players_index.json", players_index)
    save("player_yearly.json", player_yearly)
    save("player_vs_opp.json", player_vs_opp)
    save("player_venues.json", player_venues)
    save("h2h.json", h2h)
    save("team_format_stats.json", team_format)
    save("team_venue_stats.json", team_venue_out)
    save("venue_stats.json", venue_stats)
    save("venue_batters.json", venue_batters)
    save("venue_bowlers.json", venue_bowlers)
    save("venue_insights.json", venue_insights)
    save("records.json", records)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════


def main():
    from .rebuild import main as rebuild_main

    rebuild_main()


if __name__ == "__main__":
    main()
