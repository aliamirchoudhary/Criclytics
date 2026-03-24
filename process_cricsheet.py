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

Requirements:
    pip install pandas tqdm
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime, date
import pandas as pd
from tqdm import tqdm

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
RAW_DIR        = os.path.join(BASE_DIR, "data", "raw")
OUT_DIR        = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)

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
        "ties": 0, "no_result": 0, "last_result": ""
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
    # For tracking innings scores and match-level batter stats
    # Key: (match_file, batter) — score in this innings
    match_batter_score = defaultdict(int)
    match_batter_balls = defaultdict(int)
    match_batter_fours = defaultdict(int)
    match_batter_sixes = defaultdict(int)
    match_batter_dismissed = defaultdict(bool)
    match_batter_inning_seen = defaultdict(set)  # which innings a batter appeared in

    for match in tqdm(matches, desc="  Processing"):
        fmt    = match["_format"]
        mfile  = match["_file"]
        venue  = get_venue(match)
        teams  = get_teams(match)
        season = get_season(match)
        winner = get_winner(match)
        outcome = get_outcome(match)
        toss   = get_toss(match)
        innings_list = match.get("innings", [])

        # ── Match-level team/H2H stats ────────────────────────────────────────
        for team in teams:
            team_fmt[(team, fmt)]["matches"] += 1
            team_venue[(team, fmt, venue)]["matches"] += 1

        if len(teams) == 2:
            t_a, t_b = sorted(teams)
            key = (t_a, t_b, fmt)
            h2h_data[key]["matches"] += 1
            if winner == t_a:
                h2h_data[key]["team_a_wins"] += 1
                h2h_data[key]["last_result"] = f"{t_a} won"
            elif winner == t_b:
                h2h_data[key]["team_b_wins"] += 1
                h2h_data[key]["last_result"] = f"{t_b} won"
            elif outcome.get("result") in ("tie", "draw"):
                h2h_data[key]["ties"] += 1
                h2h_data[key]["last_result"] = outcome.get("result", "")
            else:
                h2h_data[key]["no_result"] += 1
                h2h_data[key]["last_result"] = "no result"

        for team in teams:
            if winner == team:
                team_fmt[(team, fmt)]["won"] += 1
                team_venue[(team, fmt, venue)]["won"] += 1
            elif winner and winner != team:
                team_fmt[(team, fmt)]["lost"] += 1
                team_venue[(team, fmt, venue)]["lost"] += 1
            elif outcome.get("result") == "tie":
                team_fmt[(team, fmt)]["tied"] += 1
            elif not winner:
                team_fmt[(team, fmt)]["nr"] += 1

        # ── Toss venue stats ──────────────────────────────────────────────────
        venue_data[venue]["matches"] += 1
        venue_data[venue]["formats"].add(fmt)
        toss_winner = toss.get("winner")
        if toss_winner:
            venue_data[venue]["toss_total"] += 1
            if toss_winner == winner:
                venue_data[venue]["toss_winner_won"] += 1

        # ── Batting first / chasing outcome ──────────────────────────────────
        if len(innings_list) >= 2 and winner:
            batting_first_team = innings_list[0].get("team", "")
            chasing_team_won = (winner != batting_first_team)
            venue_data[venue]["chase_results"].append(chasing_team_won)

        # ── Innings-level venue scoring ───────────────────────────────────────
        for i_idx, inning in enumerate(innings_list):
            bat_team = inning.get("team", "")
            inn_runs = 0; inn_wkts = 0; inn_overs = 0
            pp_runs = 0; pp_wkts = 0
            mid_runs = 0; mid_wkts = 0
            death_runs = 0; death_wkts = 0

            for over_obj in inning.get("overs", []):
                ov = over_obj.get("over", 0)
                for d in over_obj.get("deliveries", []):
                    r = d.get("runs", {}).get("total", 0)
                    inn_runs += r
                    wk = len(d.get("wickets", []))
                    inn_wkts += wk
                    # Phase split (T20I)
                    if fmt == "T20I":
                        if ov < 6:
                            pp_runs += r; pp_wkts += wk
                        elif ov < 15:
                            mid_runs += r; mid_wkts += wk
                        else:
                            death_runs += r; death_wkts += wk
                    inn_overs = ov + 1

            batting_first = (i_idx == 0)
            venue_data[venue]["innings"].append({
                "total": inn_runs, "wickets": inn_wkts,
                "overs": inn_overs, "format": fmt,
                "batting_first": batting_first
            })
            team_fmt[(bat_team, fmt)]["total_runs"]   += inn_runs
            team_fmt[(bat_team, fmt)]["total_innings"] += 1
            team_fmt[(bat_team, fmt)]["total_wkts"]   += inn_wkts
            team_venue[(bat_team, fmt, venue)]["total_runs"]    += inn_runs
            team_venue[(bat_team, fmt, venue)]["innings_count"] += 1
            if inn_runs > team_venue[(bat_team, fmt, venue)]["highest"]:
                team_venue[(bat_team, fmt, venue)]["highest"] = inn_runs

            if fmt == "T20I":
                if pp_runs:
                    venue_data[venue]["powerplay_runs"].append(pp_runs)
                    venue_data[venue]["powerplay_wkts"].append(pp_wkts)
                if mid_runs:
                    venue_data[venue]["middle_runs"].append(mid_runs)
                    venue_data[venue]["middle_wkts"].append(mid_wkts)
                if death_runs:
                    venue_data[venue]["death_runs"].append(death_runs)
                    venue_data[venue]["death_wkts"].append(death_wkts)

        # ── Delivery-level batting and bowling ────────────────────────────────
        # Reset per-match batter trackers for this match
        match_batters_this = defaultdict(lambda: {
            "runs": 0, "balls": 0, "fours": 0, "sixes": 0, "dismissed": False
        })
        match_bowlers_over = defaultdict(lambda: defaultdict(int))  # bowl -> over -> runs

        opp_map = {}
        for team in teams:
            opp = next((t for t in teams if t != team), "")
            opp_map[team] = opp

        for i_idx, over_num, d, bat_team, bowl_team in iter_deliveries(match):
            batter  = d.get("batter", "")
            bowler  = d.get("bowler", "")
            runs_b  = d.get("runs", {}).get("batter", 0)
            runs_tot = d.get("runs", {}).get("total", 0)
            is_wd_nb = is_wide_or_noball(d)
            wk_kind  = dismissal_kind(d)
            wickets  = d.get("wickets", [])

            opposition = opp_map.get(bat_team, "")
            bk = (batter, fmt)
            bvk = (batter, fmt, opposition)
            bvnk = (batter, fmt, venue)
            byk = (batter, fmt, season) if season else None

            # ── Batter runs ───────────────────────────────────────────────────
            match_batters_this[batter]["runs"]   += runs_b
            match_batters_this[batter]["balls"]  += (0 if is_wd_nb else 1)
            if runs_b == 4:
                match_batters_this[batter]["fours"] += 1
                bat[bk]["fours"] += 1
            if runs_b == 6:
                match_batters_this[batter]["sixes"] += 1
                bat[bk]["sixes"] += 1

            bat[bk]["runs"]  += runs_b
            bat[bk]["balls"] += (0 if is_wd_nb else 1)
            bat[bk]["matches"].add(mfile)

            bat_vs[bvk]["runs"]   += runs_b
            bat_vs[bvk]["balls"]  += (0 if is_wd_nb else 1)
            bat_venue[bvnk]["runs"]  += runs_b
            bat_venue[bvnk]["balls"] += (0 if is_wd_nb else 1)
            if byk:
                bat_year[byk]["runs"]  += runs_b
                bat_year[byk]["balls"] += (0 if is_wd_nb else 1)
                bat_year[byk]["matches"].add(mfile)

            venue_bat[(venue, batter)]["runs"]   += runs_b
            venue_bat[(venue, batter)]["balls"]  += (0 if is_wd_nb else 1)
            venue_bat[(venue, batter)]["matches"].add(mfile)

            # ── Wicket kind for venue stats ───────────────────────────────────
            for wk in wickets:
                venue_data[venue]["wicket_kinds"][wk.get("kind", "other")] += 1

            # ── Dismissal ─────────────────────────────────────────────────────
            for wk in wickets:
                player_out = wk.get("player_out", "")
                k = wk.get("kind", "")
                if k not in ("run out", "obstructing the field", "retired hurt"):
                    # Bowler gets credit
                    bowl[(bowler, fmt)]["wickets"] += 1
                    bowl[(bowler, fmt)]["matches"].add(mfile)
                    venue_bowl[(venue, bowler)]["wickets"] += 1
                    venue_bowl[(venue, bowler)]["matches"].add(mfile)
                # Batter dismissed
                if player_out == batter or not player_out:
                    match_batters_this[batter]["dismissed"] = True

            # ── Bowler runs ────────────────────────────────────────────────────
            if not is_wide_or_noball(d) or d.get("extras", {}).get("noballs"):
                bowl[(bowler, fmt)]["balls"] += 1
                venue_bowl[(venue, bowler)]["balls"] += 1
            bowl[(bowler, fmt)]["runs"] += runs_tot
            bowl[(bowler, fmt)]["matches"].add(mfile)
            venue_bowl[(venue, bowler)]["runs"] += runs_tot
            match_bowlers_over[bowler][over_num] += runs_tot

        # ── Post-match: finalise batter innings ────────────────────────────────
        # We need per-inning scores per batter — approximate by using per-match totals
        for batter, stats in match_batters_this.items():
            runs = stats["runs"]
            dismissed = stats["dismissed"]
            fmt2 = fmt
            bk = (batter, fmt2)
            bvk_inner = (batter, fmt2, opp_map.get("", ""))

            # Find batter's team from match
            player_team = ""
            for team, players in get_info(match).get("players", {}).items():
                if batter in players:
                    player_team = team
                    break
            opposition2 = opp_map.get(player_team, "")
            bvk = (batter, fmt2, opposition2)
            bvnk = (batter, fmt2, venue)
            byk = (batter, fmt2, season) if season else None

            bat[bk]["innings"] += 1
            if dismissed:
                bat[bk]["dismissals"] += 1
                bat_vs[bvk]["dismissals"] += 1
                bat_venue[bvnk]["dismissals"] += 1
                if byk: bat_year[byk]["dismissals"] += 1
            else:
                bat[bk]["not_outs"] += 1

            bat_vs[bvk]["innings"] += 1
            bat_venue[bvnk]["innings"] += 1
            if byk: bat_year[byk]["innings"] += 1
            venue_bat[(venue, batter)]["matches"]  # already added

            if runs >= 100:
                bat[bk]["hundreds"] += 1
                bat_vs[bvk]["hundreds"] += 1
                bat_venue[bvnk]["hundreds"] += 1
                if byk: bat_year[byk]["hundreds"] += 1
                venue_bat[(venue, batter)]["hundreds"] += 1
            elif runs >= 50:
                bat[bk]["fifties"] += 1
                bat_vs[bvk]["fifties"] += 1
                bat_venue[bvnk]["fifties"] += 1
                if byk: bat_year[byk]["fifties"] += 1

            if runs > bat[bk]["highest"]:
                bat[bk]["highest"] = runs
            if runs > bat_vs[bvk]["highest"]:
                bat_vs[bvk]["highest"] = runs
            if runs > bat_venue[bvnk]["highest"]:
                bat_venue[bvnk]["highest"] = runs
            if runs > venue_bat[(venue, batter)]["highest"]:
                venue_bat[(venue, batter)]["highest"] = runs

            bat[bk]["innings_scores"].append(runs)

        # ── Post-match: finalise bowler innings ────────────────────────────────
        # Maiden overs
        for bowler, over_runs in match_bowlers_over.items():
            bk = (bowler, fmt)
            bowl[bk]["innings"] += 1
            innings_wkts = 0
            for o_runs in over_runs.values():
                if o_runs == 0:
                    bowl[bk]["maidens"] += 1
            # Track best bowling
            # We'll compute best figures at output stage from accumulated data

        # ── Venue bowler innings ──────────────────────────────────────────────
        for batter in match_batters_this:
            venue_bat[(venue, batter)]["matches"].add(mfile)

    return {
        "bat": bat, "bowl": bowl,
        "bat_vs": bat_vs, "bat_venue": bat_venue, "bat_year": bat_year,
        "venue_data": venue_data,
        "h2h_data": h2h_data,
        "team_fmt": team_fmt, "team_venue": team_venue,
        "venue_bat": venue_bat, "venue_bowl": venue_bowl,
    }


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — COMPUTE DERIVED STATS
# ════════════════════════════════════════════════════════════════════════════

def avg(runs, dismissals):
    if dismissals == 0:
        return round(runs, 1) if runs else 0.0
    return round(runs / dismissals, 2)

def sr(runs, balls):
    if balls == 0: return 0.0
    return round(runs / balls * 100, 2)

def econ(runs, balls):
    if balls == 0: return 0.0
    return round(runs / balls * 6, 2)

def bowl_avg(runs, wickets):
    if wickets == 0: return 0.0
    return round(runs / wickets, 2)


def build_players_index(bat, bowl):
    print("\n[2/4] Building players_index …")
    # Collect all unique player names across batting and bowling
    all_players = set()
    for (player, fmt) in bat:
        all_players.add(player)
    for (player, fmt) in bowl:
        all_players.add(player)

    players = {}
    for player in all_players:
        entry = {
            "name": player,
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
                }

            bwk = (player, fmt)
            if bwk in bowl and bowl[bwk]["wickets"] > 0:
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
                }

        # Recent form — last 10 innings scores across all formats
        all_scores = []
        for fmt in ("Test", "ODI", "T20I"):
            all_scores.extend(bat.get((player, fmt), {}).get("innings_scores", []))
        entry["recent_form"] = all_scores[-10:]

        # Only include players with meaningful data
        total_matches = sum(
            len(bat.get((player, fmt), {}).get("matches", set()))
            for fmt in ("Test", "ODI", "T20I")
        )
        if total_matches >= 1:
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
    return round(sum(lst) / len(lst), 1) if lst else 0

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
            "formats":     list(data["formats"]),
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

    players_index   = build_players_index(bat, bowl)
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
    print("=" * 60)
    print("  Cricklytics — Cricsheet Pipeline")
    print("=" * 60)

    # Verify folders exist
    missing = []
    for fmt, folder in FORMAT_DIRS.items():
        if not os.path.isdir(folder):
            missing.append(f"  ✗  {folder}  ({fmt})")
    if missing:
        print("\n⚠  Missing raw data folders:")
        for m in missing:
            print(m)
        print("\nPlease unzip your Cricsheet downloads into data/raw/ like this:")
        print("  data/raw/tests_male_json/")
        print("  data/raw/odis_male_json/")
        print("  data/raw/t20s_male_json/")
        return

    print(f"\nOutput folder: {OUT_DIR}")

    start = datetime.now()
    matches       = load_all_matches()
    accumulators  = build_raw_accumulators(matches)
    save_all(accumulators, matches)

    elapsed = (datetime.now() - start).seconds
    print(f"\n✅  Done in {elapsed}s — all files written to data/processed/")
    print("=" * 60)


if __name__ == "__main__":
    main()
