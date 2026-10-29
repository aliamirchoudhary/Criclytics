"""Pure historical summary projections; scoring lives in scoring/aggregation."""

from collections import defaultdict


def avg(runs, dismissals):
    if dismissals == 0:
        return None
    return round(runs / dismissals, 2)


def sr(runs, balls):
    if balls == 0:
        return None
    return round(runs / balls * 100, 2)


def econ(runs, balls):
    if balls == 0:
        return None
    return round(runs / balls * 6, 2)


def bowl_avg(runs, wickets):
    if wickets == 0:
        return None
    return round(runs / wickets, 2)


def build_players_index(bat, bowl, player_country=None, include_bowling_only=False):
    print("\n[2/4] Building players_index …")
    if player_country is None:
        player_country = {}
    # Collect all unique player names across batting and bowling
    all_players = set()
    for player, fmt in bat:
        all_players.add(player)
    for player, fmt in bowl:
        all_players.add(player)

    players = {}
    for player in sorted(all_players):
        entry = {
            "name": player,
            "country": player_country.get(player, ""),
            "formats": [],
            "batting": {},
            "bowling": {},
            "recent_form": [],  # last 10 innings scores
        }
        for fmt in ("Test", "ODI", "T20I"):
            bk = (player, fmt)
            if bk in bat and bat[bk]["innings"] > 0:
                b = bat[bk]
                dis = b["dismissals"]
                entry["formats"].append(fmt) if fmt not in entry["formats"] else None
                entry["batting"][fmt] = {
                    "matches": len(b["matches"]),
                    "innings": b["innings"],
                    "runs": b["runs"],
                    "highest": b["highest"],
                    "average": avg(b["runs"], dis),
                    "strike_rate": sr(b["runs"], b["balls"]),
                    "hundreds": b["hundreds"],
                    "fifties": b["fifties"],
                    "fours": b["fours"],
                    "sixes": b["sixes"],
                    "not_outs": b["not_outs"],
                    "dismissals": b["dismissals"],
                    "balls": b["balls"],
                }

            bwk = (player, fmt)
            if bwk in bowl and bowl[bwk]["innings"] > 0:
                bw = bowl[bwk]
                entry["formats"].append(fmt) if fmt not in entry["formats"] else None
                entry["bowling"][fmt] = {
                    "matches": len(bw["matches"]),
                    "innings": bw["innings"],
                    "wickets": bw["wickets"],
                    "runs": bw["runs"],
                    "balls": bw["balls"],
                    "average": bowl_avg(bw["runs"], bw["wickets"]),
                    "economy": econ(bw["runs"], bw["balls"]),
                    "maidens": bw["maidens"],
                    "five_wkts": bw["five_wkts"],
                    "best_wkts": bw["best_wkts"],
                    "best_runs": bw["best_runs"],
                }

        # Recent form — last 10 innings scores across all formats
        form = [
            event
            for fmt in ("Test", "ODI", "T20I")
            for event in bat.get((player, fmt), {}).get("form_events", [])
        ]
        entry["recent_form"] = [event[3] for event in sorted(form)[-10:]]

        # Only include players with meaningful data
        total_matches = sum(
            len(bat.get((player, fmt), {}).get("matches", set()))
            for fmt in ("Test", "ODI", "T20I")
        )
        if total_matches >= 1 or (include_bowling_only and entry["bowling"]):
            players[player] = entry

    return players


def build_player_yearly(bat_year):
    print("  Building player_yearly …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, year), stats in bat_year.items():
        if year and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][str(year)] = {
                "matches": len(stats["matches"]),
                "innings": stats["innings"],
                "runs": stats["runs"],
                "average": avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "hundreds": stats["hundreds"],
                "fifties": stats["fifties"],
            }
    return {p: dict(fmts) for p, fmts in result.items()}


def build_player_vs_opp(bat_vs):
    print("  Building player_vs_opp …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, opp), stats in bat_vs.items():
        if opp and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][opp] = {
                "innings": stats["innings"],
                "runs": stats["runs"],
                "average": avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "highest": stats["highest"],
                "hundreds": stats["hundreds"],
                "fifties": stats["fifties"],
            }
    return {p: dict(fmts) for p, fmts in result.items()}


def build_player_venues(bat_venue):
    print("  Building player_venues …")
    result = defaultdict(lambda: defaultdict(dict))
    for (player, fmt, venue), stats in bat_venue.items():
        if venue and stats["innings"] > 0:
            dis = stats["dismissals"]
            result[player][fmt][venue] = {
                "innings": stats["innings"],
                "runs": stats["runs"],
                "average": avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "highest": stats["highest"],
                "hundreds": stats["hundreds"],
                "fifties": stats["fifties"],
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
            "matches": total,
            "team_a_wins": stats["team_a_wins"],
            "team_b_wins": stats["team_b_wins"],
            "ties": stats["ties"],
            "draws": stats.get("draws", 0),
            "no_result": stats["no_result"],
            "team_a_win_pct": round(stats["team_a_wins"] / total * 100, 1)
            if total
            else 0,
            "team_b_win_pct": round(stats["team_b_wins"] / total * 100, 1)
            if total
            else 0,
            "last_result": stats["last_result"],
        }
    return result


def build_team_format_stats(team_fmt):
    print("  Building team_format_stats …")
    result = defaultdict(dict)
    for (team, fmt), stats in team_fmt.items():
        m = stats["matches"]
        result[team][fmt] = {
            "matches": m,
            "won": stats["won"],
            "lost": stats["lost"],
            "tied": stats["tied"],
            "drawn": stats.get("drawn", 0),
            "no_result": stats["nr"],
            "win_pct": round(stats["won"] / m * 100, 1) if m else 0,
            "avg_score": round(stats["total_runs"] / stats["total_innings"], 1)
            if stats["total_innings"]
            else 0,
            "avg_wickets": round(stats["total_wkts"] / stats["total_innings"], 1)
            if stats["total_innings"]
            else 0,
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
            "matches": m,
            "won": stats["won"],
            "lost": stats["lost"],
            "win_pct": round(stats["won"] / m * 100, 1) if m else 0,
            "avg_score": round(stats["total_runs"] / stats["innings_count"], 1)
            if stats["innings_count"]
            else 0,
            "highest": stats["highest"],
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
            return [
                i["total"]
                for i in innings
                if i["format"] == fmt and i["batting_first"] == first
            ]

        def fmt_highest(fmt):
            totals = [i["total"] for i in innings if i["format"] == fmt]
            return max(totals) if totals else 0

        def fmt_lowest(fmt):
            totals = [
                i["total"] for i in innings if i["format"] == fmt and i["total"] > 0
            ]
            return min(totals) if totals else 0

        total_matches = data["matches"]
        chase_wins = sum(1 for r in chase_results if r)
        chase_pct = (
            round(chase_wins / len(chase_results) * 100, 1) if chase_results else 0
        )

        toss_win_pct = (
            round(data["toss_winner_won"] / data["toss_total"] * 100, 1)
            if data["toss_total"]
            else 0
        )

        # Wicket type percentages
        total_wkts = sum(data["wicket_kinds"].values())
        wkt_types = {}
        for kind, count in data["wicket_kinds"].items():
            wkt_types[kind] = round(count / total_wkts * 100, 1) if total_wkts else 0

        result[venue] = {
            "venue": venue,
            "matches": total_matches,
            "formats": sorted(data["formats"]),
            "t20i": {
                "avg_1st_innings": _safe_avg(fmt_innings("T20I", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("T20I", False)),
                "highest": fmt_highest("T20I"),
                "lowest": fmt_lowest("T20I"),
                "avg_powerplay": _safe_avg(data["powerplay_runs"]),
                "avg_middle": _safe_avg(data["middle_runs"]),
                "avg_death": _safe_avg(data["death_runs"]),
            },
            "odi": {
                "avg_1st_innings": _safe_avg(fmt_innings("ODI", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("ODI", False)),
                "highest": fmt_highest("ODI"),
                "lowest": fmt_lowest("ODI"),
            },
            "test": {
                "avg_1st_innings": _safe_avg(fmt_innings("Test", True)),
                "avg_2nd_innings": _safe_avg(fmt_innings("Test", False)),
                "highest": fmt_highest("Test"),
            },
            "chase_win_pct": chase_pct,
            "defend_win_pct": round(100 - chase_pct, 1),
            "toss_winner_win_pct": toss_win_pct,
            "wicket_types": wkt_types,
        }
        for fmt, label in (("T20I", "t20i"), ("ODI", "odi"), ("Test", "test")):
            target = result[venue].setdefault(label, {})
            chase = data.get("chase_by_format", {}).get(fmt, [])
            target["chase_samples"] = len(chase)
            target["chase_win_pct"] = (
                round(sum(chase) / len(chase) * 100, 2) if chase else None
            )
            target["innings_by_number"] = {
                str(number): _safe_avg(
                    [
                        i["total"]
                        for i in innings
                        if i["format"] == fmt and i["innings_id"] == number
                    ]
                )
                for number in (1, 2, 3, 4)
            }
            if fmt == "Test":
                target["chase_win_pct"] = None
                target.pop("avg_1st_innings", None)
                target.pop("avg_2nd_innings", None)
        # No all-format chase likelihood: choose a format explicitly.
        result[venue]["chase_win_pct"] = None
    return result


def build_venue_batters(venue_bat):
    print("  Building venue_batters …")
    result = defaultdict(list)
    for (venue, player), stats in venue_bat.items():
        if stats["runs"] < 50:
            continue
        dis = stats.get("dismissals", 1) or 1
        result[venue].append(
            {
                "player": player,
                "matches": len(stats["matches"]),
                "runs": stats["runs"],
                "average": avg(stats["runs"], dis),
                "strike_rate": sr(stats["runs"], stats["balls"]),
                "highest": stats["highest"],
                "hundreds": stats["hundreds"],
            }
        )
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
        result[venue].append(
            {
                "player": player,
                "matches": len(stats["matches"]),
                "wickets": stats["wickets"],
                "runs": stats["runs"],
                "balls": stats["balls"],
                "average": bowl_avg(stats["runs"], stats["wickets"]),
                "economy": econ(stats["runs"], stats["balls"]),
            }
        )
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
            "avg_t20_1st": stats["t20i"]["avg_1st_innings"],
            "avg_odi_1st": stats["odi"]["avg_1st_innings"],
            "chase_win_pct": stats["chase_win_pct"],
            "highest_t20": stats["t20i"]["highest"],
            "highest_odi": stats["odi"]["highest"],
            "avg_powerplay": stats["t20i"]["avg_powerplay"],
            "toss_win_pct": stats["toss_winner_win_pct"],
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
                entries.append(
                    {
                        "player": player,
                        "matches": len(stats["matches"]),
                        "runs": stats["runs"],
                        "average": avg(stats["runs"], dis),
                        "hundreds": stats["hundreds"],
                        "highest": stats["highest"],
                    }
                )
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
                entries.append(
                    {
                        "player": player,
                        "matches": len(stats["matches"]),
                        "wickets": stats["wickets"],
                        "average": bowl_avg(stats["runs"], stats["wickets"]),
                        "economy": econ(stats["runs"], stats["balls"]),
                        "five_wkts": stats["five_wkts"],
                    }
                )
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
                entries.append(
                    {
                        "player": player,
                        "matches": len(stats["matches"]),
                        "innings": stats["innings"],
                        "runs": stats["runs"],
                        "average": avg(stats["runs"], stats["dismissals"]),
                        "hundreds": stats["hundreds"],
                    }
                )
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
                entries.append(
                    {
                        "player": player,
                        "hundreds": stats["hundreds"],
                        "fifties": stats["fifties"],
                        "matches": len(stats["matches"]),
                        "average": avg(stats["runs"], stats["dismissals"]),
                    }
                )
        return sorted(entries, key=lambda x: x["hundreds"], reverse=True)[:n]

    return {
        "most_runs": {
            "Test": top_runs("Test"),
            "ODI": top_runs("ODI"),
            "T20I": top_runs("T20I"),
        },
        "most_wickets": {
            "Test": top_wickets("Test"),
            "ODI": top_wickets("ODI"),
            "T20I": top_wickets("T20I"),
        },
        "best_averages": {
            "Test": top_averages("Test", 20),
            "ODI": top_averages("ODI", 20),
            "T20I": top_averages("T20I", 10),
        },
        "most_hundreds": {
            "Test": top_hundreds("Test"),
            "ODI": top_hundreds("ODI"),
        },
    }
