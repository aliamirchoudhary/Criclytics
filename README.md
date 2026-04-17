<div align="center">

# 🏏 Cricklytics
### Context-Aware Cricket Analytics & Probability Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-orange?logo=scikit-learn)](https://scikit-learn.org)
[![Data](https://img.shields.io/badge/Data-Cricsheet-green)](https://cricsheet.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

**Cricklytics** transforms historical cricket data into contextual, probability-based insights — going far beyond career averages to answer questions like *"How likely is this batsman to score 50+ at this venue against this attack?"*

[Live Demo](#) · [Report a Bug](#) · [Data Sources](data-sources.html)

</div>

---

## ✨ Features

| Section | What it does |
|---|---|
| 🏠 **Home** | Live match cards, upcoming fixtures, trending players (real API), mini ICC rankings, recent results |
| 🗓️ **Matches** | Live / upcoming / completed match groups with full pagination and format filters |
| 👤 **Players** | 4,700+ player profiles, format stats, role & country filters, photos with initials fallback |
| 👤 **Player Profile** | Career stats, yearly breakdown, vs-opposition table, at-venues table, recent form strip, ICC rankings sidebar, ML probability insights |
| 🛡️ **Teams** | ICC-style rankings, T20I win rates, format switching |
| 🛡️ **Team Profile** | W/L donut chart, format breakdown, H2H records, squad grid, venue performance, recent results |
| 🏟️ **Venues** | Bat/bowl bias indicators, chase vs defend win %, venue cards grouped by country |
| 🏟️ **Venue Profile** | Scoring stats, pitch bias bar, top batters/bowlers, team bias tab, similar venues, probability insights |
| 📋 **Match Detail** | Full scorecard (batting + bowling), overview, context insights, H2H and venue context |
| 📅 **Match Upcoming** | Fixture info, H2H records, venue context, win probability bar |
| 🏆 **Rankings** | ICC-scraped team & player rankings (batting/bowling/all-rounder) by format with hardcoded fallback |
| 📊 **Records** | Most runs, best averages, most centuries, most wickets — all filterable by format |
| ⚖️ **Compare** | Side-by-side player & team comparison — stat grid with winner highlighting, probability bars, attribute radar |
| 🔍 **Search** | Global search across players, teams, and venues |
| 🤖 **ML Engine** | Logistic Regression predictions for batting 50+, batting 100+, team win probability — wired to all relevant pages |

---

## 🤖 Machine Learning

Cricklytics includes a real ML probability engine trained on Cricsheet historical data.

### Models

| Model | Samples | Accuracy | File |
|---|---|---|---|
| Player Batting 50+ | 14,542 | 97.24% | `models/player_batting_50_model.pkl` |
| Player Batting 100+ | 14,542 | 99.44% | `models/player_batting_100_model.pkl` |
| Team Win Prediction | 861 | 57.96% | `models/team_win_model.pkl` |
| Bowling Wickets | — | Heuristic fallback | — |
| Venue Bias | — | Static calculation | — |

### ML Endpoints

```
GET  /api/predict/player/<name>?metric=50&format=ODI
GET  /api/predict/player/<name>/all?format=ODI
POST /api/predict/team_match   { team_a, team_b, format, venue }
GET  /api/predict/venue/<name>?format=ODI
GET  /api/predict/leaderboard?metric=50&format=ODI&limit=10
GET  /api/predict/status
```

### ML Files

```
ml_models.py              — LogisticRegression training + .pkl persistence
ml_probability_engine.py  — Inference engine (scipy.stats, H2H adjustment, venue bias)
ml-widgets.js             — Frontend probability card renderer
ml-wiring-addon.js        — Shared wiring functions for all pages
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/aliamirchoudhary/criclytics.git
cd criclytics
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Open .env and fill in your API keys
```

### 5. Set up the data pipeline
```bash
# Download Cricsheet data first (see Data Setup below)
python process_cricsheet.py

# Fetch ICC rankings
python scrape_rankings.py

# Fetch live match schedule (requires VPN on some networks)
python scrape_matches.py
```

### 6. Train ML models
```bash
python ml_models.py
```

This saves trained `.pkl` files to `models/`. Flask loads them automatically at startup. Skip this step if `.pkl` files are already present.

### 7. Run the app
```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔑 API Keys

Create a `.env` file in the project root (see `.env.example`):

```env
CRICAPI_KEY=your_cricapi_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

| Key | Source | Cost | Used for |
|---|---|---|---|
| `CRICAPI_KEY` | [cricapi.com](https://cricapi.com) | Free (lifetime) | Live scores, scorecards — requires VPN on some networks |
| `RAPIDAPI_KEY` | [RapidAPI — Cricbuzz](https://rapidapi.com/cricbuzz/api/cricbuzz-cricket) | Free (500 req/month) | Weekly match schedule refresh |

> **Note:** The app works fully without API keys using locally cached data. Live/recent match data requires keys and may need a VPN on restricted networks.

---

## 📁 Project Structure

```
criclytics/
│
├── app.py                    # Flask backend — all REST API endpoints
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore
│
├── *.html (×17)              # Frontend pages (served by Flask static)
├── *.js  (×16)               # Per-page API wiring + shared utilities
├── styles.css                # Global design system
├── cricklytics.js            # Shared JS utilities (flags, search, routing)
│
├── ml_models.py              # ML training pipeline (LogisticRegression)
├── ml_probability_engine.py  # ML inference engine (scipy.stats)
├── ml-widgets.js             # Frontend probability card renderer
├── ml-wiring-addon.js        # Shared ML wiring for all pages
│
├── models/                   # Trained .pkl files (auto-created by ml_models.py)
│   ├── player_batting_50_model.pkl
│   ├── player_batting_50_scaler.pkl
│   ├── player_batting_100_model.pkl
│   ├── player_batting_100_scaler.pkl
│   ├── team_win_model.pkl
│   └── team_win_scaler.pkl
│
├── data/
│   ├── raw/                  # Cricsheet ZIP downloads (gitignored)
│   ├── processed/            # Generated by process_cricsheet.py (gitignored)
│   ├── live/                 # Generated by scrapers (gitignored)
│   └── static/               # Reference files committed to repo
│       ├── players_meta.json # Player metadata & photo URLs (168 players)
│       ├── teams_meta.json   # Team metadata
│       └── venues_meta.json  # Venue metadata
│
├── process_cricsheet.py      # Parses Cricsheet ball-by-ball data → analytics JSON
├── scrape_matches.py         # Weekly match schedule scraper (Cricbuzz)
├── scrape_rankings.py        # ICC rankings scraper with hardcoded fallback
├── fetch_live.py             # CricAPI live data + scorecard fetcher
├── fetch_photos.py           # Player photo fetcher (Wikipedia fallback)
├── create_static_files.py    # Generates initial static JSON reference files
│
└── docs/
    ├── Iteration_1.docx      # Sprint 1 documentation
    ├── Iteration_2.docx      # Sprint 2 documentation
    └── README.md
```

> **Why flat structure?** Flask is configured with `static_folder="."` to serve all frontend files directly from the project root. Splitting into `frontend/` and `backend/` would require updating path references across 17 HTML files and 16 JS files. The flat layout is intentional and appropriate for this architecture.

---

## 📊 Data Setup

Cricklytics uses [Cricsheet](https://cricsheet.org) as its primary data source (CC BY-SA 4.0).

### Download Cricsheet data
1. Go to [cricsheet.org/downloads](https://cricsheet.org/downloads/)
2. Download these ZIP files into `data/raw/`:
   - `t20s_male_json.zip` → extract to `data/raw/t20s_male_json/`
   - `odis_male_json.zip` → extract to `data/raw/odis_male_json/`
   - `tests_male_json.zip` → extract to `data/raw/tests_male_json/`
3. Run `python process_cricsheet.py`

This generates all analytics files in `data/processed/` (~5–10 minutes for full dataset).

### What gets generated

| File | Contents |
|---|---|
| `players_index.json` | All players with career stats per format |
| `player_yearly.json` | Year-by-year batting/bowling per player |
| `player_vs_opp.json` | Per-player stats vs each opposition |
| `player_venues.json` | Per-player stats at each venue |
| `team_format_stats.json` | Per-team win/loss/avg per format |
| `h2h.json` | Head-to-head records for every team pair |
| `venue_stats.json` | Per-venue scoring and outcome stats |
| `venue_batters.json` | Top run-scorers at each venue |
| `venue_bowlers.json` | Top wicket-takers at each venue |
| `records.json` | All-time records across formats |

---

## 🔧 Scripts Reference

| Script | What it does | When to run |
|---|---|---|
| `process_cricsheet.py` | Parses all Cricsheet JSONs → analytics JSON | Once after downloading Cricsheet data |
| `ml_models.py` | Trains LogisticRegression models → saves .pkl files | Once, or when retraining is needed |
| `scrape_matches.py` | Fetches live/recent/upcoming fixtures from Cricbuzz | Weekly |
| `scrape_rankings.py` | Fetches ICC rankings (falls back to hardcoded if blocked) | When rankings need refreshing |
| `fetch_live.py` | Fetches live scores + scorecards from CricAPI | When live data is needed (may need VPN) |
| `fetch_photos.py` | Fetches missing player photos from Wikipedia | When new players need photos |
| `create_static_files.py` | Generates initial static JSON reference files | Once during setup |

---

## 🌐 API Endpoints

### Data Endpoints (Cricsheet)
```
GET /api/players               — All players with career stats
GET /api/players/<name>        — Full profile for one player
GET /api/teams                 — All teams with format stats
GET /api/teams/<name>          — Full team profile with H2H and venue stats
GET /api/venues                — All venues
GET /api/venues/<name>         — Full venue profile with top batters/bowlers
GET /api/records               — All-time records across formats
GET /api/h2h                   — Head-to-head between two teams
GET /api/compare/players       — Side-by-side player comparison
GET /api/search                — Global search across players, teams, venues
GET /api/rankings              — Rankings computed from Cricsheet data
GET /api/icc-rankings          — Scraped ICC rankings with hardcoded fallback
```

### Live Data Endpoints (CricAPI — cached)
```
GET /api/live                  — Live match scores (cached, falls back to live.json)
GET /api/matches               — All fixtures (cached, falls back to matches.json)
GET /api/matches/<id>          — Single match detail
GET /api/matches/<id>/score    — Live scorecard
GET /api/series                — Active series list
```

### ML Prediction Endpoints
```
GET  /api/predict/player/<name>       — Single metric prediction
GET  /api/predict/player/<name>/all   — All metrics for a player
POST /api/predict/team_match          — Match outcome prediction
GET  /api/predict/venue/<name>        — Venue performance bias
GET  /api/predict/leaderboard         — Top players by predicted metric
GET  /api/predict/status              — ML model health check
```

### Static Metadata Endpoints
```
GET /api/meta/players          — players_meta.json (photos, DOB, ISO codes)
GET /api/meta/players/<name>   — Single player metadata
GET /api/meta/teams            — teams_meta.json
GET /api/meta/venues           — venues_meta.json
GET /api/status                — Backend health check (all data files)
```

---

## 🔄 Data Flow

```
Cricsheet ZIPs
      │
      ▼
process_cricsheet.py  ──►  data/processed/*.json (12 files)
                                    │
                                    ▼
                              Flask app.py  ◄──  scrape_rankings.py
                                    │                    │
                              /api/* endpoints    ICC Rankings
                                    │             (or hardcoded fallback)
                                    ▼
                           *-api.js files  ◄──  ml_probability_engine.py
                                    │                    ▲
                              HTML Pages           ml_models.py
                                                  (trained .pkl files)

CricAPI ──► fetch_cricapi() ──► data/live/*.json (cache)
                                    │
                                    ▼
                              /api/live, /api/matches
```

---

## ⚠️ Network Notes

- **CricAPI** (`api.cricapi.com`) may time out on restricted networks. All live endpoints fall back to cached JSON files in `data/live/`.
- **ICC Rankings scraper** may be blocked. `scrape_rankings.py` falls back to hardcoded March 2026 rankings via `build_hardcoded_rankings()`.
- **Cricbuzz** (match schedule) requires a RapidAPI key. Without it, `matches.json` serves from cache.
- The app is **fully functional offline** using cached data — no page will crash without a network connection.

---

## ⚠️ Disclaimer

All probability figures and statistical insights on Cricklytics are **historical frequency estimates** derived from past match data. They are not predictions of future outcomes and must not be used for gambling or betting decisions. See the [full disclaimer](disclaimer.html).

---

## 👥 Team

| Name | Roll No. | Role |
|---|---|---|
| Muhammad Ali Aamir | 24L-2558 | Backend, Flask API, Data Pipeline, ML Engine |
| Muhammad Mahad Mahmood | 24L-2548 | Frontend, UI/UX, JS Integration, ML Wiring, Testing |

---

## 📅 Iteration Status

| Iteration | Status | Key Deliverables |
|---|---|---|
| **Iteration 1** | ✅ Complete | UI shell, all listing pages, data pipeline, Flask API, match detail, search |
| **Iteration 2** | ✅ Complete | Player/team/venue profiles, ML engine, compare tool, rankings, records, full responsiveness audit |
| **Iteration 3** | 🔄 Planned | Advanced ML models, real-time updates, performance optimisation |

---

## 📄 Data Attribution

- Ball-by-ball match data: [Cricsheet](https://cricsheet.org) — [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- Live data: [CricAPI](https://cricapi.com) · [Cricbuzz via RapidAPI](https://rapidapi.com/cricbuzz/api/cricbuzz-cricket)
- Country flags: [country-flag-emoji-json](https://www.npmjs.com/package/country-flag-emoji-json) via jsDelivr CDN
- Player photos: CricAPI CDN · Wikipedia REST API

---

<div align="center">
<sub>Built with ♥ for cricket analytics · FAST-NUCES · Spring 2026</sub>
</div>
