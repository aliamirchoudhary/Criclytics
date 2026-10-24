---
title: Cricklytics (Final Production Version)
emoji: 🏏
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

<div align="center">

<img src="https://img.shields.io/badge/🏏-CRICLYTICS-1E6091?style=for-the-badge&labelColor=0D1B2A" alt="Criclytics"/>

# Criclytics
### Context-Aware Cricket Analytics & Probability Platform

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![JavaScript](https://img.shields.io/badge/JS-Vanilla_ES6-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Deployment](https://img.shields.io/badge/Live-Hugging_Face_Spaces-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/spaces)
[![Frontend](https://img.shields.io/badge/Frontend-Cloudflare_Workers-F38020?style=flat-square&logo=cloudflare&logoColor=white)](https://workers.cloudflare.com)
[![Data](https://img.shields.io/badge/Data-Cricsheet_CC_BY--SA_4.0-2DB24A?style=flat-square)](https://cricsheet.org)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Completed_%26_Deployed-1D9E75?style=flat-square)](https://criclytics.aliamirchoudhary.workers.dev/)

<br/>

> **Criclytics** transforms historical cricket data into contextual, probability-based insights —  
> going far beyond career averages to answer questions like  
> *"How likely is this batsman to score 50+ at this venue against this attack?"*

<br/>

**[🌐 Live Demo](https://criclytics.aliamirchoudhary.workers.dev/) · [🐛 Report a Bug](mailto:aliamirchoudhary@gmail.com) · [📊 Data Sources](https://cricsheet.org)**

<br/>

---

</div>

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [The Innovation: Mega-Enrichment](#-the-innovation-mega-enrichment-pipeline)
- [Features](#-features)
- [Machine Learning Engine](#-machine-learning-engine)
- [Architecture](#️-architecture)
- [Quick Start & Setup](#-quick-start--setup)
- [API Keys](#-api-keys)
- [Project Structure](#-project-structure)
- [Data Setup](#-data-setup)
- [API Reference](#-api-reference)
- [Scripts Reference](#-scripts-reference)
- [Production Deployment](#-production-deployment-hugging-face-spaces)
- [Testing & QA](#-testing--qa)
- [Iteration History](#-iteration-history)
- [Team](#-team)
- [Data Attribution](#-data-attribution)
- [Disclaimer](#️-disclaimer)

---

## 🌟 Project Overview

**Criclytics** is a full-stack, multi-page cricket analytics web application built at Our team for the modern cricket fan, analyst, and data scientist. Unlike conventional cricket websites that show isolated statistics, Criclytics layers a **Machine Learning probability engine** on top of 6,200+ enriched international matches to answer the questions that raw scoreboards never could.

The platform covers all three major international formats — **T20I, ODI, and Test** — across dedicated sections for Players, Teams, Venues, Matches, Rankings, Records, Compare, and Search. Every probability output is accompanied by a mandatory statistical disclaimer.

| | |
|---|---|
| **Version** | 3.0 — Final Production Release |
| **Status** | Completed & Deployed |

---

## 🚀 The Innovation: Mega-Enrichment Pipeline

The core technical breakthrough of the final release is the **Mega-Enrichment Pipeline** — a solution to the "Production Data Gap" problem.

### The Problem
Hosting 6,200+ individual Cricsheet JSON files on production is impossible — Git has a 10 MB file limit, and storage quotas make raw file serving infeasible on platforms like Hugging Face Spaces.

### The Solution

```
Raw Cricsheet (6,200+ files)
         │
         ▼  process_cricsheet.py
   ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐
   │  Filter 1   │───▶│   Filter 2   │───▶│     Filter 3      │───▶│      Filter 4        │
   │  Parsing    │    │ Aggregation  │    │ Mega-Enrichment   │    │   Compression        │
   │ validate +  │    │ scorecards + │    │ join officials,   │    │  merge all records   │
   │  extract    │    │ partnerships │    │ venue, toss data  │    │  → single JSON sink  │
   └─────────────┘    └──────────────┘    └───────────────────┘    └──────────────────────┘
                                                                              │
                                                                              ▼
                                                               completed_matches.json (~93 MB)
                                                               6,200+ matches · full data parity
```

| Benefit | Detail |
|---|---|
| **No Raw Files at Runtime** | Production server never touches individual Cricsheet JSONs |
| **O(1) Lookups** | Flask performs a simple dictionary lookup instead of O(N) file scans |
| **Sub-200ms Responses** | All complex joins pre-calculated at build-time, not request-time |
| **Smart Pathing** | `app.py` checks `data/processed/` (local dev) then `/` (HF root) automatically |

---

## ✨ Features

<details>
<summary><strong>🏠 Home Page</strong></summary>

- Live match cards with real-time scores via CricAPI
- Upcoming fixtures with countdown
- Trending players and mini ICC rankings sidebar
- Recent results carousel

</details>

<details>
<summary><strong>🗓️ Matches</strong></summary>

- Live / Upcoming / Completed match groups with full pagination
- Format filters (T20I / ODI / Test)
- Match detail pages with three tabs: Overview · Scorecard · Context Insights
- Full innings scorecard with batting + bowling tables
- Win Probability Bar powered by ML engine
- Venue and H2H context for upcoming fixtures

</details>

<details>
<summary><strong>👤 Players</strong></summary>

- 4,700+ player profiles with format-wise career stats
- Role & country filters with photo grid (initials fallback)
- Yearly breakdown, vs-opposition table, at-venues table
- Recent form strip with trend visualization
- ICC rankings sidebar
- ML probability insights (50+, 100+, 2+ wickets)

</details>

<details>
<summary><strong>🛡️ Teams</strong></summary>

- ICC-style rankings with T20I win rates
- W/L donut chart per format
- Full H2H records against every opponent
- Squad grid and venue performance breakdown
- Win probability insights

</details>

<details>
<summary><strong>🏟️ Venues</strong></summary>

- Bat/bowl bias indicators
- Chase vs defend win % 
- Top run-scorers and wicket-takers at each venue
- Team bias tab and similar venues
- Venue probability insights

</details>

<details>
<summary><strong>⚖️ Compare Tool</strong></summary>

- **Player vs Player** — side-by-side stats with format tabs (T20/ODI/Test), venue & opposition overlays, ML probability bars
- **Team vs Team** — H2H win/loss breakdown, venue-specific records, win probability insights
- Winner highlighting on every stat row

</details>

<details>
<summary><strong>🏆 Rankings & Records</strong></summary>

- ICC-scraped team & player rankings (Batting / Bowling / All-rounder) by format
- Hardcoded March 2026 fallback when ICC blocks the scraper
- All-time records filterable by Format, Team, Player, Venue
- Clickable records linking to full profiles

</details>

<details>
<summary><strong>🔍 Global Search</strong></summary>

- Persistent search bar in global header across all 17 pages
- Categorized results: Players · Teams · Venues · Matches
- 2-character minimum trigger with debouncing to prevent API spam

</details>

---

## 🤖 Machine Learning Engine

Criclytics includes a production-grade ML probability engine trained on Cricsheet historical data.

### Models

| Model | Training Samples | Accuracy | File |
|---|---|---|---|
| Player Batting 50+ | 14,542 | **97.24%** | `models/player_batting_50_model.pkl` |
| Player Batting 100+ | 14,542 | **99.44%** | `models/player_batting_100_model.pkl` |
| Team Win Prediction | 861 | **57.96%** | `models/team_win_model.pkl` |
| Bowling Wickets | — | Heuristic fallback | — |
| Venue Bias | — | Static calculation | — |

### ML Architecture

```
Historical Cricsheet Data
         │
         ▼
  ml_models.py  ──── LogisticRegression training ────▶  models/*.pkl
         │
         ▼
ml_probability_engine.py  ◄──── loaded at Flask startup
         │
         ├──▶ H2H adjustment factor (team win model)
         ├──▶ Venue bias coefficient
         ├──▶ Career stats feature vector
         └──▶ Probability score [0.0 – 1.0]  ──▶  REST API  ──▶  Frontend bars
```

### ML Endpoints

```
GET  /api/predict/player/<name>?metric=50&format=ODI    — Single metric prediction
GET  /api/predict/player/<name>/all?format=ODI          — All metrics for a player  
POST /api/predict/team_match  { team_a, team_b, format, venue }  — Match outcome
GET  /api/predict/venue/<name>?format=ODI               — Venue performance bias
GET  /api/predict/leaderboard?metric=50&format=ODI      — Top players by metric
GET  /api/predict/status                                — ML model health check
```

> ⚠️ **Disclaimer:** All probability figures are historical frequency estimates derived from past match data. They are not predictions of future outcomes and must not be used for gambling or betting decisions.

---

## 🏛️ Architecture

Criclytics uses **Client-Server Architecture** as its primary pattern, combined with a **Pipe-and-Filter** data pipeline.

```
┌──────────────────────────────────┐         ┌─────────────────────────────────────┐
│         CLIENT LAYER             │         │           SERVER LAYER              │
│     Cloudflare Workers           │         │        Hugging Face Spaces          │
│                                  │         │                                     │
│  User Browser                    │         │  Flask REST Server (app.py)         │
│       │                          │         │       │                             │
│  HTML / CSS (17 pages)           │  HTTP   │  ML Probability Engine              │
│       │                REST/JSON │◀───────▶│       │                             │
│  Vanilla JS (16 modules)         │         │  Data Access Layer                  │
│       │                          │         │       │                             │
│  Fetch API                       │         │  completed_matches.json (93 MB)     │
└──────────────────────────────────┘         └─────────────────────────────────────┘
```

### Architectural Patterns

| Pattern | Where Used | Purpose |
|---|---|---|
| **Client-Server** | Entire system | Decoupled thick client + stateless REST API |
| **Pipe-and-Filter** | `process_cricsheet.py` | ETL pipeline: Parse → Aggregate → Enrich → Compress |
| **Smart Path** | `app.py`, `ml_models.py`, `ml_probability_engine.py` | Auto-detects local vs production data paths |
| **Repository** | Data access layer | Uniform JSON lookup interface |
| **Fallback Chain** | Live API, Rankings, ML | Graceful degradation when external services fail |

---

## 🚀 Quick Start & Setup

### Prerequisites

- Python **3.11+**
- Git
- ~500 MB free disk space (for Cricsheet data)

### 1. Clone the Repository

```bash
git clone https://github.com/aliamirchoudhary/criclytics.git
cd criclytics
```

### 2. Create & Activate Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your keys (see API Keys section below)
```

### 5. Download & Process Cricsheet Data

```bash
# Download Cricsheet ZIPs → data/raw/ (see Data Setup section)
python process_cricsheet.py    # ~5–10 min — generates all analytics JSON
```

### 6. Train ML Models

```bash
python ml_models.py            # Generates .pkl files in models/
```

> Skip this step if `.pkl` files are already present.

### 7. (Optional) Refresh Live Data & Rankings

```bash
python scrape_rankings.py      # ICC rankings (falls back to hardcoded if blocked)
python scrape_matches.py       # Fixture schedule (requires RapidAPI key)
```

### 8. Run the App

```bash
python app.py
```

Open **[http://localhost:5000](http://localhost:5000)** in your browser. 🎉

---

## 🔑 API Keys

Create a `.env` file in the project root:

```env
CRICAPI_KEY=your_cricapi_key_here
RAPIDAPI_KEY=your_rapidapi_key_here
```

| Key | Source | Free Tier | Used For |
|---|---|---|---|
| `CRICAPI_KEY` | [cricapi.com](https://cricapi.com) | Lifetime free | Live scores, scorecards |
| `RAPIDAPI_KEY` | [RapidAPI — Cricbuzz](https://rapidapi.com/cricbuzz/api/cricbuzz-cricket) | 500 req/month | Weekly match schedule |

> **No keys?** The app runs fully offline using cached data. No page will crash without network access.

---

## 📁 Project Structure

```
criclytics/
│
├── app.py                       # Flask backend — all REST API routes
├── process_cricsheet.py         # Mega-Enrichment ETL pipeline
├── ml_models.py                 # ML training (LogisticRegression → .pkl)
├── ml_probability_engine.py     # ML inference engine
├── scrape_rankings.py           # ICC rankings scraper + hardcoded fallback
├── scrape_matches.py            # Cricbuzz match schedule fetcher
├── fetch_live.py                # CricAPI live scores + scorecard fetcher
├── fetch_photos.py              # Player photo fetcher (Wikipedia fallback)
├── create_static_files.py       # Generates initial static JSON reference files
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
│
├── *.html (×17)                 # Frontend pages (served by Flask static_folder=".")
├── *.js  (×16)                  # Per-page API wiring + shared utilities
├── styles.css                   # Global design system (dark-mode)
├── cricklytics.js               # Shared JS utilities (flags, search, routing)
├── ml-widgets.js                # Frontend probability card renderer
├── ml-wiring-addon.js           # Shared ML wiring for all pages
│
├── models/                      # Trained .pkl files (auto-created by ml_models.py)
│   ├── player_batting_50_model.pkl
│   ├── player_batting_50_scaler.pkl
│   ├── player_batting_100_model.pkl
│   ├── player_batting_100_scaler.pkl
│   ├── team_win_model.pkl
│   └── team_win_scaler.pkl
│
├── data/
│   ├── raw/                     # Cricsheet ZIP downloads          [gitignored]
│   ├── processed/               # Generated by process_cricsheet.py [gitignored]
│   ├── live/                    # CricAPI cache (*.json)            [gitignored]
│   └── static/                  # Reference files committed to repo
│       ├── players_meta.json    # Player metadata & photo URLs (168 players)
│       ├── teams_meta.json      # Team metadata
│       └── venues_meta.json     # Venue metadata
│
└── documentation/
    ├── architecture_reference.md
    ├── iteration_3_final.md
    ├── iteration_3_original.md
    ├── project_overview_and_business_case.md
    └── testing_and_qa_reference.md
```

> **Why flat structure?** Flask is configured with `static_folder="."` to serve all frontend files directly from the project root. This is intentional — splitting into `frontend/` and `backend/` would require updating path references across 17 HTML files and 16 JS files.

---

## 📊 Data Setup

Criclytics uses [Cricsheet](https://cricsheet.org) as its primary data source (CC BY-SA 4.0).

### Download Cricsheet Data

1. Go to **[cricsheet.org/downloads](https://cricsheet.org/downloads/)**
2. Download these ZIP files into `data/raw/`:

| ZIP File | Extract To |
|---|---|
| `t20s_male_json.zip` | `data/raw/t20s_male_json/` |
| `odis_male_json.zip` | `data/raw/odis_male_json/` |
| `tests_male_json.zip` | `data/raw/tests_male_json/` |

3. Run `python process_cricsheet.py` (~5–10 min)

### Generated Files

| File | Contents |
|---|---|
| `completed_matches.json` | **Mega-enriched** full match records (93 MB — upload manually to HF) |
| `players_index.json` | All players with career stats per format |
| `player_yearly.json` | Year-by-year batting/bowling per player |
| `player_vs_opp.json` | Per-player stats vs each opposition |
| `player_venues.json` | Per-player stats at each venue |
| `team_format_stats.json` | Per-team win/loss/avg per format |
| `h2h.json` | Head-to-head records for every team pair |
| `venue_stats.json` | Per-venue scoring and outcome stats |
| `records.json` | All-time records across formats |

---

## 📡 API Reference

### Cricsheet Data Endpoints
```
GET /api/players                   — All players with career stats
GET /api/players/<name>            — Full player profile
GET /api/teams                     — All teams with format stats
GET /api/teams/<name>              — Full team profile (H2H + venue stats)
GET /api/venues                    — All venues
GET /api/venues/<name>             — Full venue profile
GET /api/records                   — All-time records
GET /api/h2h                       — Head-to-head between two teams
GET /api/compare/players           — Side-by-side player comparison
GET /api/search                    — Global search (players + teams + venues + matches)
GET /api/rankings                  — Cricsheet-computed rankings
GET /api/icc-rankings              — Scraped ICC rankings with hardcoded fallback
```

### Live Data Endpoints *(CricAPI — cached)*
```
GET /api/live                      — Live match scores (falls back to live.json)
GET /api/matches                   — All fixtures (falls back to matches.json)
GET /api/matches/<id>              — Single match detail
GET /api/matches/<id>/score        — Live scorecard
GET /api/series                    — Active series list
```

### ML Prediction Endpoints
```
GET  /api/predict/player/<name>    — Single metric prediction
GET  /api/predict/player/<name>/all — All metrics for a player
POST /api/predict/team_match       — Match outcome prediction
GET  /api/predict/venue/<name>     — Venue performance bias
GET  /api/predict/leaderboard      — Top players by predicted metric
GET  /api/predict/status           — ML model health check
```

### Metadata Endpoints
```
GET /api/meta/players              — players_meta.json
GET /api/meta/players/<name>       — Single player metadata
GET /api/meta/teams                — teams_meta.json
GET /api/meta/venues               — venues_meta.json
GET /api/status                    — Backend health check (all data files)
```

---

## 🔧 Scripts Reference

| Script | Purpose | When to Run |
|---|---|---|
| `process_cricsheet.py` | Parses all Cricsheet JSONs → Mega-Enriched analytics | Once after downloading Cricsheet data |
| `ml_models.py` | Trains LogisticRegression → saves `.pkl` files | Once, or when retraining is needed |
| `scrape_rankings.py` | Fetches ICC rankings (hardcoded fallback if blocked) | When rankings need refreshing |
| `scrape_matches.py` | Fetches live/recent/upcoming fixtures (Cricbuzz) | Weekly |
| `fetch_live.py` | Fetches live scores + scorecards from CricAPI | When live data is needed |
| `fetch_photos.py` | Fetches missing player photos from Wikipedia | When new players need photos |
| `create_static_files.py` | Generates initial static JSON reference files | Once during setup |

---

## 🌐 Production Deployment (Hugging Face Spaces)

The backend is deployed on **Hugging Face Spaces** (Python/Docker SDK). The frontend is served via **Cloudflare Workers**.

### Why Not Standard Git Deploy?

Git has a **10 MB file size limit**. Our production data files are:
- `completed_matches.json` — ~93 MB
- `players_index.json` — large
- `models/*.pkl` — large

These **cannot** be committed to Git and must be uploaded manually.

### Step-by-Step Deployment

#### 1. Push Code via Git
```bash
# Add Hugging Face as a remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/criclytics

# Push code (HTML, JS, CSS, Python — no large data files)
git push hf main
```

#### 2. Upload Large Files Manually via HF Web UI

Go to your Hugging Face Space → **Files** tab → upload these to the **root directory**:

| File | Size | Notes |
|---|---|---|
| `completed_matches.json` | ~93 MB | Generated by `process_cricsheet.py` |
| `players_index.json` | varies | Generated by `process_cricsheet.py` |
| `models/player_batting_50_model.pkl` | small | Generated by `ml_models.py` |
| `models/player_batting_100_model.pkl` | small | Generated by `ml_models.py` |
| `models/team_win_model.pkl` | small | Generated by `ml_models.py` |
| `models/*.scaler.pkl` | small | Generated by `ml_models.py` |

#### 3. Smart Path — How It Works

Once uploaded to HF root, the app auto-detects them:

```python
# Smart Path logic in app.py
DATA_PATHS = [
    "data/processed/completed_matches.json",  # Local dev
    "/completed_matches.json",                 # HF Spaces root
    "completed_matches.json"                   # Fallback
]
```

No code changes needed between local development and production.

#### 4. .gitignore (Keep Your Repo Clean)

```gitignore
# Large data files — upload manually to HF
data/raw/
data/processed/
data/live/
completed_matches.json
players_index.json

# ML models — regenerate or upload manually
models/*.pkl

# Environment
.env
__pycache__/
*.pyc
venv/
```

---

## 🧪 Testing & QA

Criclytics applies two formal black-box testing methodologies:

### Boundary Value Analysis (BVA)

| Test Area | Min | Min+ | Nominal | Max- | Max | Status |
|---|---|---|---|---|---|---|
| Over calculation (balls) | 0 balls → `0.0` | 1 ball → `0.1` | 3 balls → `0.3` | 5 balls → `0.5` | 6 balls → `1.0` | ✅ Pass |
| ML Win Probability | `0.000` — empty bar | `0.001` — near-zero | `0.500` — equal chance | `0.999` — near-full | `1.000` — 100% | ✅ Pass |
| Search input length | 1 char — suppressed | 2 chars — triggers API | 50 chars — normal | — | 255+ chars — no crash | ✅ Pass |
| Match margin | 0 runs → Tie/No Result | 1 run → "Won by 1 run" | typical margin | — | — | ✅ Pass |

### Equivalence Partitioning (EP)

| Partition | Classes | Result |
|---|---|---|
| Match formats | Limited Overs (ODI/T20I) · Unlimited Overs (Test) | ✅ Pass |
| Player roles | Batsmen · Bowlers · All-rounders | ✅ Pass |
| Missing data | Missing venue → "Unknown Venue" · Abandoned → "No data" | ✅ Pass |

### Manual QA Checklist

- [x] Rankings: "Last Updated" timestamp present
- [x] Compare: selecting same player twice handled gracefully
- [x] Context Insights: Win probability bars appear for all completed matches
- [x] Search: clicking a result navigates to correct profile/match
- [x] Mobile: all 17 pages scale correctly at 375px viewport

---

## 📅 Iteration History

### ✅ Iteration 1 — Foundation (Weeks 1–2)
- Dark-mode UI shell with 17 core pages
- Data ingestion pipeline (`process_cricsheet.py` v1)
- Flask REST API with all base endpoints
- Match listing, player/team/venue listing pages
- Global search (categorized results)
- Match detail page with full scorecard

### ✅ Iteration 2 — Analysis & ML (Weeks 3–4)
- Player, Team, Venue profile pages with deep analytics
- ML engine: LogisticRegression trained on 14,542 samples
- Compare tool (Player vs Player, Team vs Team) with winner highlighting
- ICC Rankings scraper with hardcoded fallback
- Records section (all-time filterable)
- Full mobile responsiveness audit across all 17 pages

### ✅ Iteration 3 — Production & Enrichment (Weeks 5–6)
- **Mega-Enrichment Pipeline**: 6,200+ matches → single 93 MB JSON
- **Smart Path Architecture**: single codebase, two environments
- **Production Deployment**: Hugging Face Spaces + Cloudflare Workers
- Global Search System with debouncing
- Advanced Compare Tool (format tabs, ML bars, venue overlays)
- Rankings & Records (enhanced filtering, clickable records)
- BVA & Integration testing across all modules
- `.gitignore` cleanup, Git repo optimization

---

## ⚠️ Network Notes

| Service | Issue | Fallback |
|---|---|---|
| **CricAPI** (`api.cricapi.com`) | May time out on restricted networks | Serves from `data/live/*.json` cache |
| **ICC Rankings scraper** | May be blocked by ICC CDN | `build_hardcoded_rankings()` — March 2026 data |
| **Cricbuzz / RapidAPI** | Requires API key | Serves from cached `matches.json` |
| **Player Photos** | Wikipedia CDN variability | Initials avatar fallback |

The app is **fully functional offline** — no page crashes without a network connection.

---

## 👥 Team

| Role | Responsibilities |
|---|---|
| **Backend & ML Lead** | Flask API, Data Pipeline, Mega-Enrichment, ML Training, HF Deployment, Architecture |
| **Frontend & QA Lead** | UI/UX (17 pages), JS Integration, ML Wiring, Testing, Mobile Responsiveness |

---

## 📄 Data Attribution

| Source | License | Used For |
|---|---|---|
| [Cricsheet](https://cricsheet.org) | CC BY-SA 4.0 | Ball-by-ball match data (primary database) |
| [CricAPI](https://cricapi.com) | Free tier | Live scores and scorecards |
| [Cricbuzz via RapidAPI](https://rapidapi.com/cricbuzz/api/cricbuzz-cricket) | Free tier | Match schedule |
| [country-flag-emoji-json](https://www.npmjs.com/package/country-flag-emoji-json) | MIT | Country flags via jsDelivr CDN |
| Wikipedia REST API | CC BY-SA 3.0 | Player photos fallback |

---

## ⚠️ Disclaimer

All probability figures and statistical insights on Criclytics are **historical frequency estimates** derived from past match data using Logistic Regression models. They are **not predictions of future outcomes** and must not be used for gambling, betting, or financial decisions.

Criclytics is an analytics platform built for educational and research purposes only.

---

<div align="center">

**[🌐 Live Demo](https://criclytics.aliamirchoudhary.workers.dev/)**

<br/>

Built with ♥ for cricket fans, analysts, and data scientists worldwide.

</div>
