# Criclytics Data Audit

Snapshot date: 2026-08-10

This file documents the data sources currently used by Criclytics, what data is already present in the repo, and the main gaps that need to be filled before training stronger next-ball prediction models.

## 1) Data sources currently in use

| Source | Where it is used | What it provides |
|---|---|---|
| Cricsheet (CC BY-SA 4.0) | `process_cricsheet.py`, `scrape_matches.py`, `app.py`, `ml_models.py`, `ml_probability_engine.py` | Historical ball-by-ball male international match data for Tests, ODIs, and T20Is. This is the main training corpus for player, team, and venue analytics. |
| CricAPI | `fetch_live.py`, `fetch_schedule.py`, `fetch_photos.py`, `app.py` | Live matches, fixtures, series metadata, scorecards, match details, and player photos. Used as the main live data source and fallback for fixtures. |
| Cricbuzz via RapidAPI | `scrape_matches.py` and live/fixture helpers | Live scorecard and fixture data when available through the Cricbuzz API endpoints. |
| ICC official rankings | `scrape_rankings.py`, `data/live/rankings.json` | Team and player rankings for batting, bowling, and all-rounder categories across formats. |
| ICC schedule fallback | `fetch_schedule.py` | Hardcoded ICC 2026 fallback schedule for fixtures when live APIs are unavailable. |
| Wikipedia REST API | `fetch_photos.py` | Supplementary player thumbnails when CricAPI does not provide an image. |
| `country-flag-emoji-json` | Frontend pages and metadata rendering | Country flag SVGs used throughout the UI. |
| Font Awesome | Frontend pages | Icons used in navigation, cards, filters, tabs, and score sections. |
| Local static metadata | `data/static/*.json`, `create_static_files.py` | Curated player, team, and venue metadata used as a permanent reference layer. |

## 2) What data we currently have

### Raw historical corpus

| Dataset | Current size |
|---|---:|
| Raw Cricsheet files: ODI | 2,521 |
| Raw Cricsheet files: T20I | 3,255 |
| Raw Cricsheet files: Test | 878 |
| Total raw Cricsheet files | 6,654 |

### Processed historical corpus

| Dataset | Current size |
|---|---:|
| Completed international matches in `data/processed/completed_matches.json` | 6,246 |
| Player index in `players_index.json` | 4,812 players |
| Yearly player stats in `player_yearly.json` | 4,812 players |
| Player vs opposition stats in `player_vs_opp.json` | 4,812 players |
| Player at venue stats in `player_venues.json` | 4,812 players |
| Team format stats in `team_format_stats.json` | 109 teams |
| Team venue stats in `team_venue_stats.json` | 108 team/venue entries |
| Head-to-head records in `h2h.json` | 1,034 team pairs |
| Venue stats in `venue_stats.json` | 463 venues |
| Venue batting leaders in `venue_batters.json` | 452 venues |
| Venue bowling leaders in `venue_bowlers.json` | 449 venues |
| Venue insights in `venue_insights.json` | 463 venues |
| Records dataset in `records.json` | 4 top-level sections |

### Local reference metadata

| Dataset | Current size |
|---|---:|
| Featured player metadata in `data/static/players_meta.json` | 168 players |
| Featured player metadata with image URLs | 115 players |
| Team metadata in `data/static/teams_meta.json` | 12 teams |
| Venue metadata in `data/static/venues_meta.json` | 11 venues with pitch profiles |

### Live cache / runtime data

| Dataset | Current size |
|---|---:|
| `data/live/live.json` | 25 live matches |
| `data/live/matches.json` | 25 match/fixture entries |
| `data/live/series.json` | 25 series entries |
| `data/live/rankings.json` | 3 player ranking groups and 3 team ranking groups |
| `data/live/*.json` cache files total | 11 files |

## 3) What data we are short of

The current repo is strong on historical batting, match, venue, and rankings coverage, but it is still missing several data layers needed for next-ball prediction and richer bowling/fielding models.

| Missing or weak area | Current situation | What we need next |
|---|---|---|
| Ball-level bowling context | We have bowling summaries in player and venue datasets, but not a dedicated next-ball training table with phase-by-phase bowler context. | Ball-by-ball bowling features, spells, over phase, line/length proxies, dismissal context, matchups, and momentum features. |
| Fielding data | There is no dedicated fielding event dataset exposed in the current processed assets. | Catches, run-outs, stumpings, fielder identity, missed chances, fielding positions, and pressure-based fielding outcomes. |
| Weather data | No match-time weather feed is stored in the current data layer. | Temperature, humidity, wind, rain probability, dew, and forecast/actual weather at venue and match time. |
| Live pitch conditions | Venue metadata has static pitch profiles for 11 venues, but not per-match pitch state. | Match-day pitch reports, pitch deterioration, pace/spin assistance by innings, and toss-adjusted pitch behavior. |
| Live pressure features | We have historical match outcomes, but not a dedicated next-ball state table. | Runs required, wickets in hand, partnership, recent form window, over phase, boundary streaks, target context, and win-probability state per ball. |
| Playing XI / lineup data | Not systematically stored as a model feature layer. | Confirmed XI, batting order, bowling order, substitutes/impact player where relevant, and player availability/injury/news flags. |
| Broader player coverage | `players_meta.json` covers 168 featured players, but only 115 have image URLs. | More player profiles, more image coverage, and deeper bowler-specific metadata. |
| Venue coverage for pitch profiles | Only 11 venues have hand-curated static pitch profiles. | Pitch profiles for the full venue set, plus dimensions, boundary lengths, and venue-specific behavior by format. |
| Non-international coverage | The historical corpus is primarily male international cricket. | Domestic leagues, women’s cricket, age-group cricket, and tournament-specific context if the model should generalize beyond internationals. |

## 4) Data that already helps the model

These existing fields are a good base for a next-ball model, even though they are not sufficient on their own:

- Batter and bowler summaries in `players_index.json`
- Yearly player form in `player_yearly.json`
- Opposition-specific player splits in `player_vs_opp.json`
- Venue-specific player splits in `player_venues.json`
- Team format and venue strengths in `team_format_stats.json` and `team_venue_stats.json`
- Venue aggregate behavior in `venue_stats.json`, `venue_batters.json`, `venue_bowlers.json`, and `venue_insights.json`
- Match results and scorecards in `completed_matches.json`
- Live fixtures and rankings caches in `data/live/*.json`
- Static pitch metadata in `data/static/venues_meta.json`

## 5) Recommended next data additions

To move from current summary models to next-ball prediction, the next data pass should ideally add:

1. Ball-by-ball enriched bowling and batting tables.
2. Fielding event extraction.
3. Weather integration by venue and match time.
4. Match-day pitch and dew context.
5. Playing XI, batting order, and bowling order features.
6. Pressure-situation features from live score state.
7. Larger player image and metadata coverage.
8. Optional expansion into women’s, domestic, and league data if the model should generalize beyond male internationals.

## 6) Bottom line

Criclytics already has a strong historical core:

- 6,654 raw Cricsheet match files
- 6,246 completed matches in the processed corpus
- 4,812 players in the main player index
- 463 venue records with aggregate stats
- 1,034 head-to-head team pairs

The biggest gaps for a real next-ball model are not raw match counts, but missing contextual features: fielding, detailed bowling events, weather, pitch state, and live match pressure context.

Once those are added, the model can move from broad probability estimates toward ball-by-ball outcome prediction.
