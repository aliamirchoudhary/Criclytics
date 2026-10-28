---
title: Criclytics
emoji: "🏏"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Criclytics

Cricket history, contextual analysis, and a planned next-delivery probability
platform. The legacy statistics and probability engine are under audit and are
not yet suitable for coaching decisions. See [the audit](docs/AUDIT.md).

## Start here

- [Audit and verified weaknesses](docs/AUDIT.md)
- [Architecture, paths and deployment migration](docs/ARCHITECTURE.md)
- [Product roadmap and $0 constraints](docs/ROADMAP.md)
- [Ticket index](tickets.md) and [implementation tickets](tickets/)
- [Branch workflow](docs/GIT_WORKFLOW.md)
- [Original reports and notes](docs/history/)

## Local setup

Use Python 3.11 or 3.12 in a virtual environment:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open http://localhost:5000. `flask --app criclytics_app:create_app run` is an
alternative. Network feeds and Redis are disabled by default, even when keys
exist. `LIVE_FETCH_ENABLED=1` explicitly enables them. Never commit `.env`.
Dependencies currently have known advisory findings; T002 is a release blocker.

A clean clone does not include historical/live/model artifacts. Keep Cricsheet
JSON in `data/raw/{t20s_male_json,odis_male_json,tests_male_json}/`, then run:

```powershell
python -m criclytics_app.pipeline.cricsheet
```

**The legacy pipeline has known cricket-statistics defects (T009).** Generating
artifacts does not certify their correctness. Existing datasets have been left
unchanged during the folder migration. Curated reference files remain in
`data/static/`. Original .pkl artifacts remain in `models/`; the web engine does
not serve them. Do not load model files from untrusted sources.

## Layout

Application code is under `criclytics_app/`: `api/`, `web/`, `services/`, `ml/`,
`pipeline/`, `integrations/`, `templates/`, and `static/`. Build utilities are in
`scripts/`, optional diagnostics in `tools/`, checks in `tests/`, documentation in
`docs/`, and specifications in `tickets/`. Only launchers/configuration and
repository entry documents remain at the root. The existing `criclytics/` folder
is an ignored local virtual environment, not application source.

Existing page URLs and all 30 `/api/` routes remain available. API analytics are
preserved for migration compatibility, including defects documented in the audit.
Public static files use `/static/`; checkout/data/config files are not served.

## Checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q criclytics_app scripts tools app.py wsgi.py
```

With the original local data snapshot, also run:

```powershell
$env:CRICLYTICS_FULL_DATA_TESTS='1'
python -m unittest discover -s tests -v
```

This checks 12 captured API responses. It intentionally requires the old data
snapshot and is not the future statistical correctness suite. Run `node --check`
for changed JS. Optional Playwright browser checks:
`python -m tools.browser_audit` after installing Playwright and Chrome. They use
local data, block third-party assets, and write ignored evidence to `build/audit`.

## Deployment

Backend: `gunicorn --bind 0.0.0.0:7860 --workers 1 --threads 2 wsgi:app` or Docker.
Use `python -m scripts.stage_backend` to create an allowlisted HF upload artifact;
never upload the whole checkout. Provide ignored datasets separately.

Frontend: `python -m scripts.build_frontend` creates `dist/` for Cloudflare static
assets. Direct Wrangler CLI commands include this build hook. In Cloudflare
Workers Builds, explicitly set **Build command** to that Python command before
the preview/deploy command. See [exact settings](docs/CLOUDFLARE_DEPLOYMENT.md).
Remote hosting settings have not been changed here. Main-only HF release is gated
on offline tests and dependency scanning; current vulnerabilities intentionally
block it until repaired. Nothing has been deployed from this work branch.

## Data and limitations

Historical data is from [Cricsheet](https://cricsheet.org/), under its published
licensing terms. Live integrations exist for CricAPI/Cricbuzz and rankings, but
availability, rights, quotas and timely next-delivery coverage need revalidation.
Do not describe this subset of matches as a player's complete official career.
The project has no paid-service or credit-card budget. Full source/cost gates and
honest fallback modes are part of the roadmap.
