"""
process_cricsheet.py
====================
Cricklytics — Cricsheet Data Pipeline (Source B)
Processes all male international match JSON files from Cricsheet and
produces pre-computed JSON cache files for the Flask backend.

Usage:
    python process_cricsheet.py

Expected folder structure (unzip your downloads here):
    data/
        raw/
            tests_male_json/       ← unzipped contents of tests_male_json.zip
            odis_male_json/        ← unzipped contents of odis_male_json.zip
            t20s_male_json/        ← unzipped contents of t20s_male_json.zip
        processed/                 ← output folder (auto-created)

Output files in data/processed/:
    players_index.json      — all players with career stats per format
    player_yearly.json      — year-by-year batting/bowling stats per player
    player_vs_opp.json      — per-player stats vs each opposition
    player_venues.json      — per-player stats at each venue
    team_format_stats.json  — per-team format breakdown
    team_venue_stats.json   — per-team stats at each venue
    h2h.json                — head-to-head records for every team pair
    venue_stats.json        — per-venue scoring and outcome stats
    venue_batters.json      — top run-scorers at each venue
    venue_bowlers.json      — top wicket-takers at each venue
    venue_insights.json     — pre-computed highlight figures for Home/Matches sidebar
    records.json            — all-time records across formats
    completed_matches.json  — all completed international matches (for /api/matches)

Requirements:
    pip install pandas tqdm
"""

from ..paths import PROJECT_ROOT
import json
import os
import glob
from collections import defaultdict
from datetime import datetime, date
import pandas as pd
from tqdm import tqdm

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = str(PROJECT_ROOT)
RAW_DIR        = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR        = os.path.join(BASE_DIR, "data", "processed")


FORMAT_DIRS = {
    "Test": os.path.join(RAW_DIR, "tests_male_json"),
    "ODI":  os.path.join(RAW_DIR, "odis_male_json"),
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
                data["_file"]   = os.path.basename(filepath)
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
    return match.get('_scored') or score_match(match)


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
            status_text = outcome.get('result') or 'no result'
        scored = build_mega_enriched_view(match)
        scores = [{'team': inn['team'], 'r': inn['total'], 'w': inn['wickets'],
                   'o': inn['overs'], 'inning': inn['team'] + ' Innings ' + str(inn['innings_id']),
                   'super_over': inn['super_over']} for inn in scored['innings']]

        # MEGA-ENRICHMENT: Build full scorecard and officials
        officials = info.get("officials", {})
        mega_view = scored

        completed.append({
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
            "match_referee": ((officials or {}).get("match_referees") or [""])[0] if isinstance(officials, dict) else "",
            "umpires": (officials or {}).get("umpires", []) if isinstance(officials, dict) else [],
            "tv_umpires": (officials or {}).get("tv_umpires", []) if isinstance(officials, dict) else [],
            "reserve_umpires": (officials or {}).get("reserve_umpires", []) if isinstance(officials, dict) else [],
            "players": info.get("players", {}),
            "squads": info.get("players", {}),
            "score": scores,
            "innings": mega_view.get("innings", []),
            "partnerships": mega_view.get("partnerships", []),
            "match_stats": mega_view.get("match_stats", {}),
            "matchStarted": True,
            "matchEnded": True,
            "winners": [winner] if winner else [],
            "player_of_match": info.get("player_of_match", [])
        })

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
    bat = defaultdict(lambda: {
        "matches": set(), "innings": 0, "runs": 0, "balls": 0,
        "fours": 0, "sixes": 0, "fifties": 0, "hundreds": 0,
        "highest": 0, "not_outs": 0, "dismissals": 0,
        "innings_scores": []  # list of scores for form
    })

    # ── Player bowling stats ─────────────────────────────────────────────────
    bowl = defaultdict(lambda: {
        "matches": set(), "innings": 0, "balls": 0, "runs": 0,
        "wickets": 0, "maidens": 0, "five_wkts": 0,
        "best_wkts": 0, "best_runs": 999,
        "innings_wickets": []
    })

    # ── Player vs opposition (batting) ───────────────────────────────────────
    # Key: (player, format, opposition)
    bat_vs = defaultdict(lambda: {
        "innings": 0, "runs": 0, "balls": 0, "dismissals": 0,
        "highest": 0, "hundreds": 0, "fifties": 0
    })

    # ── Player at venue (batting) ─────────────────────────────────────────────
    # Key: (player, format, venue)
    bat_venue = defaultdict(lambda: {
        "innings": 0, "runs": 0, "balls": 0, "dismissals": 0,
        "highest": 0, "hundreds": 0, "fifties": 0
    })

    # ── Player yearly (batting) ───────────────────────────────────────────────
    # Key: (player, format, year)
    bat_year = defaultdict(lambda: {
        "matches": set(), "innings": 0, "runs": 0, "balls": 0,
        "dismissals": 0, "hundreds": 0, "fifties": 0
    })

    # ── Venue scoring stats ───────────────────────────────────────────────────
    # Key: venue
    venue_data = defaultdict(lambda: {
        "formats": set(),
        "matches": 0,
        "innings": [],          # list of {"total", "wickets", "overs", "format", "batting_first"}
        "chase_results": [],    # list of True/False (chasing team won?)
        "toss_winner_won": 0,
        "toss_total": 0,
        "wicket_kinds": defaultdict(int),
        "powerplay_runs": [], "powerplay_wkts": [],
        "middle_runs": [],     "middle_wkts": [],
        "death_runs": [],      "death_wkts": [],
    })

    # ── Team H2H ──────────────────────────────────────────────────────────────
    # Key: (team_a, team_b, format) — always sorted alphabetically
    h2h_data = defaultdict(lambda: {
        "matches": 0, "team_a_wins": 0, "team_b_wins": 0,
        "ties": 0, "draws": 0, "no_result": 0, "last_result": ""
    })

    # ── Team format stats ─────────────────────────────────────────────────────
    # Key: (team, format)
    team_fmt = defaultdict(lambda: {
        "matches": 0, "won": 0, "lost": 0, "tied": 0, "nr": 0,
        "total_runs": 0, "total_innings": 0, "total_wkts": 0
    })

    # ── Team venue stats ──────────────────────────────────────────────────────
    # Key: (team, format, venue)
    team_venue = defaultdict(lambda: {
        "matches": 0, "won": 0, "lost": 0,
        "total_runs": 0, "innings_count": 0, "highest": 0
    })

    # ── Venue batter/bowler stats ─────────────────────────────────────────────
    # Key: (venue, player)
    venue_bat = defaultdict(lambda: {
        "matches": set(), "runs": 0, "balls": 0, "dismissals": 0,
        "highest": 0, "hundreds": 0
    })
    venue_bowl = defaultdict(lambda: {
        "matches": set(), "balls": 0, "runs": 0, "wickets": 0,
        "best_wkts": 0, "best_runs": 999
    })

    # ── Per-match tracker ─────────────────────────────────────────────────────
    player_country = {}
    from .aggregation import aggregate
    return aggregate(matches, locals())



def avg(runs, dismissals):
    if dismissals == 0:
        return None
    return round(runs / dismissals, 2)

def sr(runs, balls):
    if balls == 0: return None
    return round(runs / balls * 100, 2)

def econ(runs, balls):
    if balls == 0: return None
    return round(runs / balls * 6, 2)

def bowl_avg(runs, wickets):
    if wickets == 0: return None
    return round(runs / wickets, 2)


def build_players_index(bat, bowl, player_country=None, include_bowling_only=False):
    print("\n[2/4] Building players_index …")
    if player_country is None:
        player_country = {}
    # Collect all unique player names across batting and bowling
    all_players = set()
    for (player, fmt) in bat:
        all_players.add(player)
    for (player, fmt) in bowl:
        all_players.add(player)

    players = {}
    for player in sorted(all_players):
        entry = {
            "name": player,
            "country": player_country.get(player, ""),
            "formats": [],
            "batting": {},
            "bowling": {},
            "recent_form": [],   # last 10 innings scores
        }
        for fmt in ("Test", "ODI", "T20I"):
            bk = (player, fmt)
            if bk in bat and bat[bk]["innings"] > 0:
                b = bat[bk]
                dis = b["dismissals"]
                entry["formats"].append(fmt) if fmt not in entry["formats"] else None
                entry["batting"][fmt] = {
                    "matches":    len(b["matches"]),
                    "innings":    b["innings"],
                    "runs":       b["runs"],
                    "highest":    b["highest"],
                    "average":    avg(b["runs"], dis),
                    "strike_rate": sr(b["runs"], b["balls"]),
                    "hundreds":   b["hundreds"],
                    "fifties":    b["fifties"],
                    "fours":      b["fours"],
                    "sixes":      b["sixes"],
                    "not_outs":   b["not_outs"],
                    "dismissals": b["dismissals"],
                    "balls": b["balls"],
                }

            bwk = (player, fmt)
            if bwk in bowl and bowl[bwk]["innings"] > 0:
                bw = bowl[bwk]
                entry["formats"].append(fmt) if fmt not in entry["formats"] else None
                entry["bowling"][fmt] = {
                    "matches":   len(bw["matches"]),
                    "innings":   bw["innings"],
                    "wickets":   bw["wickets"],
                    "runs":      bw["runs"],
                    "balls":     bw["balls"],
                    "average":   bowl_avg(bw["runs"], bw["wickets"]),
                    "economy":   econ(bw["runs"], bw["balls"]),
                    "maidens":   bw["maidens"],
                    "five_wkts": bw["five_wkts"],
                    "best_wkts": bw["best_wkts"],
                    "best_runs": bw["best_runs"],
                }

        # Recent form — last 10 innings scores across all formats
        form = [event for fmt in ('Test', 'ODI', 'T20I')
                for event in bat.get((player, fmt), {}).get('form_events', [])]
        entry['recent_form'] = [event[3] for event in sorted(form)[-10:]]

        # Only include players with meaningful data
        total_matches = sum(
            len(bat.get((player, fmt), {}).get("matches", set()))
            for fmt in ("Test", "ODI", "T20I")
        )
        if total_matches >= 1 or (include_bowling_only and entry['bowling']):
            players[player] = entry

    return players


def build_player_yearly(bat_year):
    print("  Building player_yearly …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, year), stats in bat_year.items():
        if year and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][str(year)] = {
                "matches":  len(stats["matches"]),
                "innings":  stats["innings"],
                "runs":     stats["runs"],
                "average":  avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "hundreds": stats["hundreds"],
                "fifties":  stats["fifties"],
            }
    return {p: dict(fmts) for p, fmts in result.items()}


def build_player_vs_opp(bat_vs):
    print("  Building player_vs_opp …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, opp), stats in bat_vs.items():
        if opp and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][opp] = {
                "innings":   stats["innings"],
                "runs":      stats["runs"],
                "average":   avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "highest":   stats["highest"],
                "hundreds":  stats["hundreds"],
                "fifties":   stats["fifties"],
            }
    return {p: dict(fmts) for p, fmts in result.items()}


def build_player_venues(bat_venue):
    print("  Building player_venues …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, venue), stats in bat_venue.items():
        if venue and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][venue] = {
                "innings":   stats["innings"],
                "runs":      stats["runs"],
                "average":   avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "highest":   stats["highest"],
                "hundreds":  stats["hundreds"],
                "fifties":   stats["fifties"],
            }
    return {p: dict(fmts) for p, fmts in result.items()}


def build_h2h(h2h_data):
    print("  Building h2h …")
    result = {}
    for (t_a, t_b, fmt), stats in h2h_data.items():
        key = f"{t_a}|{t_b}|{fmt}"
        total = stats["matches"]
        result[key] = {
            "team_a": t_a,
            "team_b": t_b,
            "format": fmt,
            "matches":     total,
            "team_a_wins": stats["team_a_wins"],
            "team_b_wins": stats["team_b_wins"],
            "ties":        stats["ties"],
            "draws": stats.get("draws", 0),
            "no_result":   stats["no_result"],
            "team_a_win_pct": round(stats["team_a_wins"] / total * 100, 1) if total else 0,
            "team_b_win_pct": round(stats["team_b_wins"] / total * 100, 1) if total else 0,
            "last_result": stats["last_result"],
        }
    return result


def build_team_format_stats(team_fmt):
    print("  Building team_format_stats …")
    result = defaultdict(dict)
    for (team, fmt), stats in team_fmt.items():
        m = stats["matches"]
        result[team][fmt] = {
            "matches":    m,
            "won":        stats["won"],
            "lost":       stats["lost"],
            "tied":       stats["tied"],
            "drawn": stats.get("drawn", 0),
            "no_result":  stats["nr"],
            "win_pct":    round(stats["won"] / m * 100, 1) if m else 0,
            "avg_score":  round(stats["total_runs"] / stats["total_innings"], 1)
                          if stats["total_innings"] else 0,
            "avg_wickets": round(stats["total_wkts"] / stats["total_innings"], 1)
                           if stats["total_innings"] else 0,
        }
    return {t: dict(fmts) for t, fmts in result.items()}


def build_team_venue_stats(team_venue):
    print("  Building team_venue_stats …")
    result = defaultdict(lambda: defaultdict(dict))
    for (team, fmt, venue), stats in team_venue.items():
        m = stats["matches"]
        if m < 2:
            continue
        result[team][fmt][venue] = {
            "matches":    m,
            "won":        stats["won"],
            "lost":       stats["lost"],
            "win_pct":    round(stats["won"] / m * 100, 1) if m else 0,
            "avg_score":  round(stats["total_runs"] / stats["innings_count"], 1)
                          if stats["innings_count"] else 0,
            "highest":    stats["highest"],
        }
    return {t: {f: dict(vs) for f, vs in fmts.items()} for t, fmts in result.items()}


def _safe_avg(lst):
    return round(sum(lst) / len(lst), 1) if lst else None

def build_venue_stats(venue_data):
    print("  Building venue_stats …")
    result = {}
    for venue, data in venue_data.items():
        innings = data["innings"]
        chase_results = data["chase_results"]

        # Split innings by format and first/second
        def fmt_innings(fmt, first):
            return [i["total"] for i in innings
                    if i["format"] == fmt and i["batting_first"] == first]

        def fmt_highest(fmt):
            totals = [i["total"] for i in innings if i["format"] == fmt]
            return max(totals) if totals else 0

        def fmt_lowest(fmt):
            totals = [i["total"] for i in innings if i["format"] == fmt and i["total"] > 0]
            return min(totals) if totals else 0

        total_matches = data["matches"]
        chase_wins = sum(1 for r in chase_results if r)
        chase_pct  = round(chase_wins / len(chase_results) * 100, 1) if chase_results else 0

        toss_win_pct = round(
            data["toss_winner_won"] / data["toss_total"] * 100, 1
        ) if data["toss_total"] else 0

        # Wicket type percentages
        total_wkts = sum(data["wicket_kinds"].values())
        wkt_types = {}
        for kind, count in data["wicket_kinds"].items():
            wkt_types[kind] = round(count / total_wkts * 100, 1) if total_wkts else 0

        result[venue] = {
            "venue":       venue,
            "matches":     total_matches,
            "formats":     sorted(data["formats"]),
            "t20i": {
                "avg_1st_innings": _safe_avg(fmt_innings("T20I", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("T20I", False)),
                "highest":         fmt_highest("T20I"),
                "lowest":          fmt_lowest("T20I"),
                "avg_powerplay":   _safe_avg(data["powerplay_runs"]),
                "avg_middle":      _safe_avg(data["middle_runs"]),
                "avg_death":       _safe_avg(data["death_runs"]),
            },
            "odi": {
                "avg_1st_innings": _safe_avg(fmt_innings("ODI", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("ODI", False)),
                "highest":         fmt_highest("ODI"),
                "lowest":          fmt_lowest("ODI"),
            },
            "test": {
                "avg_1st_innings": _safe_avg(fmt_innings("Test", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("Test", False)),
                "highest":         fmt_highest("Test"),
            },
            "chase_win_pct":    chase_pct,
            "defend_win_pct":   round(100 - chase_pct, 1),
            "toss_winner_win_pct": toss_win_pct,
            "wicket_types":     wkt_types,
        }
        for fmt, label in (('T20I', 't20i'), ('ODI', 'odi'), ('Test', 'test')):
            target = result[venue].setdefault(label, {})
            chase = data.get('chase_by_format', {}).get(fmt, [])
            target['chase_samples'] = len(chase)
            target['chase_win_pct'] = round(sum(chase) / len(chase) * 100, 2) if chase else None
            target['innings_by_number'] = {str(number): _safe_avg([i['total'] for i in innings
                if i['format'] == fmt and i['innings_id'] == number]) for number in (1, 2, 3, 4)}
            if fmt == 'Test':
                target['chase_win_pct'] = None
                target.pop('avg_1st_innings', None)
                target.pop('avg_2nd_innings', None)
        # No all-format chase likelihood: choose a format explicitly.
        result[venue]['chase_win_pct'] = None
    return result


def build_venue_batters(venue_bat):
    print("  Building venue_batters …")
    result = defaultdict(list)
    for (venue, player), stats in venue_bat.items():
        if stats["runs"] < 50:
            continue
        dis = stats.get("dismissals", 1) or 1
        result[venue].append({
            "player":    player,
            "matches":   len(stats["matches"]),
            "runs":      stats["runs"],
            "average":   avg(stats["runs"], dis),
            "strike_rate": sr(stats["runs"], stats["balls"]),
            "highest":   stats["highest"],
            "hundreds":  stats["hundreds"],
        })
    # Sort each venue by runs desc, keep top 10
    return {
        v: sorted(batters, key=lambda x: x["runs"], reverse=True)[:10]
        for v, batters in result.items()
    }


def build_venue_bowlers(venue_bowl):
    print("  Building venue_bowlers …")
    result = defaultdict(list)
    for (venue, player), stats in venue_bowl.items():
        if stats["wickets"] < 3:
            continue
        result[venue].append({
            "player":  player,
            "matches": len(stats["matches"]),
            "wickets": stats["wickets"],
            "runs":    stats["runs"],
            "balls":   stats["balls"],
            "average": bowl_avg(stats["runs"], stats["wickets"]),
            "economy": econ(stats["runs"], stats["balls"]),
        })
    return {
        v: sorted(bowlers, key=lambda x: x["wickets"], reverse=True)[:10]
        for v, bowlers in result.items()
    }


def build_venue_insights(venue_stats):
    """Pre-computed highlight figures for Home and Matches sidebar panels."""
    print("  Building venue_insights …")
    insights = {}
    for venue, stats in venue_stats.items():
        insights[venue] = {
            "avg_t20_1st":   stats["t20i"]["avg_1st_innings"],
            "avg_odi_1st":   stats["odi"]["avg_1st_innings"],
            "chase_win_pct": stats["chase_win_pct"],
            "highest_t20":   stats["t20i"]["highest"],
            "highest_odi":   stats["odi"]["highest"],
            "avg_powerplay":  stats["t20i"]["avg_powerplay"],
            "toss_win_pct":  stats["toss_winner_win_pct"],
        }
    return insights


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RECORDS
# ════════════════════════════════════════════════════════════════════════════

def build_records(bat, bowl, matches):
    print("\n[3/4] Building records …")

    # Most runs per format
    def top_runs(fmt, n=10):
        entries = []
        seen = set()
        for (player, f), stats in bat.items():
            if f != fmt or player in seen:
                continue
            seen.add(player)
            dis = stats["dismissals"]
            if stats["runs"] > 0:
                entries.append({
                    "player": player,
                    "matches": len(stats["matches"]),
                    "runs":    stats["runs"],
                    "average": avg(stats["runs"], dis),
                    "hundreds": stats["hundreds"],
                    "highest": stats["highest"],
                })
        return sorted(entries, key=lambda x: x["runs"], reverse=True)[:n]

    # Most wickets per format
    def top_wickets(fmt, n=10):
        entries = []
        seen = set()
        for (player, f), stats in bowl.items():
            if f != fmt or player in seen:
                continue
            seen.add(player)
            if stats["wickets"] > 0:
                entries.append({
                    "player":  player,
                    "matches": len(stats["matches"]),
                    "wickets": stats["wickets"],
                    "average": bowl_avg(stats["runs"], stats["wickets"]),
                    "economy": econ(stats["runs"], stats["balls"]),
                    "five_wkts": stats["five_wkts"],
                })
        return sorted(entries, key=lambda x: x["wickets"], reverse=True)[:n]

    # Best batting averages (min innings)
    def top_averages(fmt, min_innings=20, n=10):
        entries = []
        seen = set()
        for (player, f), stats in bat.items():
            if f != fmt or player in seen:
                continue
            seen.add(player)
            if stats["innings"] >= min_innings and stats["dismissals"] > 0:
                entries.append({
                    "player":   player,
                    "matches":  len(stats["matches"]),
                    "innings":  stats["innings"],
                    "runs":     stats["runs"],
                    "average":  avg(stats["runs"], stats["dismissals"]),
                    "hundreds": stats["hundreds"],
                })
        return sorted(entries, key=lambda x: x["average"], reverse=True)[:n]

    # Most centuries
    def top_hundreds(fmt, n=10):
        entries = []
        seen = set()
        for (player, f), stats in bat.items():
            if f != fmt or player in seen:
                continue
            seen.add(player)
            if stats["hundreds"] > 0:
                entries.append({
                    "player":   player,
                    "hundreds": stats["hundreds"],
                    "fifties":  stats["fifties"],
                    "matches":  len(stats["matches"]),
                    "average":  avg(stats["runs"], stats["dismissals"]),
                })
        return sorted(entries, key=lambda x: x["hundreds"], reverse=True)[:n]

    return {
        "most_runs": {
            "Test": top_runs("Test"),
            "ODI":  top_runs("ODI"),
            "T20I": top_runs("T20I"),
        },
        "most_wickets": {
            "Test": top_wickets("Test"),
            "ODI":  top_wickets("ODI"),
            "T20I": top_wickets("T20I"),
        },
        "best_averages": {
            "Test": top_averages("Test", 20),
            "ODI":  top_averages("ODI",  20),
            "T20I": top_averages("T20I", 10),
        },
        "most_hundreds": {
            "Test": top_hundreds("Test"),
            "ODI":  top_hundreds("ODI"),
        },
    }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — SAVE ALL OUTPUTS
# ════════════════════════════════════════════════════════════════════════════

def save_all(accumulators, matches):
    print("\n[4/4] Saving output files …")

    bat        = accumulators["bat"]
    bowl       = accumulators["bowl"]
    bat_vs     = accumulators["bat_vs"]
    bat_venue  = accumulators["bat_venue"]
    bat_year   = accumulators["bat_year"]
    venue_data = accumulators["venue_data"]
    h2h_data   = accumulators["h2h_data"]
    team_fmt   = accumulators["team_fmt"]
    team_venue = accumulators["team_venue"]
    venue_bat  = accumulators["venue_bat"]
    venue_bowl = accumulators["venue_bowl"]
    player_country = accumulators.get("player_country", {})

    players_index   = build_players_index(bat, bowl, player_country)
    player_yearly   = build_player_yearly(bat_year)
    player_vs_opp   = build_player_vs_opp(bat_vs)
    player_venues   = build_player_venues(bat_venue)
    h2h             = build_h2h(h2h_data)
    team_format     = build_team_format_stats(team_fmt)
    team_venue_out  = build_team_venue_stats(team_venue)
    venue_stats     = build_venue_stats(venue_data)
    venue_batters   = build_venue_batters(venue_bat)
    venue_bowlers   = build_venue_bowlers(venue_bowl)
    venue_insights  = build_venue_insights(venue_stats)
    records         = build_records(bat, bowl, matches)

    save("players_index.json",     players_index)
    save("player_yearly.json",     player_yearly)
    save("player_vs_opp.json",     player_vs_opp)
    save("player_venues.json",     player_venues)
    save("h2h.json",               h2h)
    save("team_format_stats.json", team_format)
    save("team_venue_stats.json",  team_venue_out)
    save("venue_stats.json",       venue_stats)
    save("venue_batters.json",     venue_batters)
    save("venue_bowlers.json",     venue_bowlers)
    save("venue_insights.json",    venue_insights)
    save("records.json",           records)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    from .rebuild import main as rebuild_main
    rebuild_main()


if __name__ == '__main__':
    main()
