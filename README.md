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

Cricket history, source-ID scouting and an experimental next-delivery shadow
workflow. Public predictions remain unavailable: the current historical model
has not passed prospective promotion gates. Original data is preserved; corrected
dataset/identity candidates require explicit selection. See [progress](docs/SESSION_PROGRESS.md)
and [release readiness](docs/OPERATIONS_RUNBOOK.md).

## Start here

- [Current audit and fixes](docs/PRE_PLAN_AUDIT.md), [remediation/migration](docs/AUDIT_REMEDIATION.md)
- [Original baseline audit (historical)](docs/AUDIT.md)
- [Architecture, paths and deployment migration](docs/ARCHITECTURE.md)
- [Current platform plan](docs/CRICKET_PLATFORM_MASTER_PLAN.md) and [plan review](docs/PLATFORM_PLAN_REVIEW.md)
- [Ticket index](tickets.md) and [implementation tickets](tickets/)
- [Branch workflow](docs/GIT_WORKFLOW.md)
- [Identity-correct statistics](docs/PLAYER_ID_AGGREGATES.md), [scouting/private plans](docs/COACH_SCOUTING.md)
- [Local shadow API](docs/FORECAST_API.md), [workspace](docs/WORKSPACE_UI.md), [prospective evaluation](docs/SHADOW_EVALUATION.md)
- [Original reports and notes](docs/history/)

## Local setup

Use Python 3.11 or 3.12 in a virtual environment:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install --require-hashes -r requirements.txt
python app.py
```

Default startup serves the UI but reports historical data unavailable until you
select `DATASET_STORE` (recommended), or an explicit private `PROCESSED_DIR`.
For deliberate local inspection of the old archive only, set `LEGACY_DATA_ENABLED=1`;
this does not fix its known statistical defects. No checkout-root fallback exists.

Open http://localhost:5000. `flask --app criclytics_app:create_app run` is an
alternative. Network feeds and Redis are disabled by default, even when keys
exist. A flag/key alone does not approve network collection: the source-policy
allowlist is currently empty. Manual scoring and historical replay are supported
locally. For a new setup, `.env.example` documents optional settings; preserve any
existing `.env` and never commit it. The pinned runtime dependency audit found no
known advisories on 2026-10-29; that is not proof of absent application defects.

A clean clone does not include historical/live/model artifacts. Keep Cricsheet
JSON in `data/raw/{t20s_male_json,odis_male_json,tests_male_json}/`, then run:

```powershell
python -m criclytics_app.pipeline.cricsheet --output build/dataset-candidate
```

The current rebuild uses the validated per-innings scorer and emits a private
manifest-bound candidate. Follow [dataset validation/selection](docs/DATASETS.md)
and [source-ID regeneration](docs/PLAYER_ID_AGGREGATES.md) before enabling corrected
player summaries; old name-keyed files retain known collision/coverage defects.
No candidate is automatically promoted. Curated reference files remain in
`data/static/`. Original .pkl artifacts remain in `models/`; the web engine does
not serve them. Do not load model files from untrusted sources.

## Layout

Application code is under `criclytics_app/`: `api/`, `web/`, `services/`, `ml/`,
`pipeline/`, `integrations/`, `templates/`, and `static/`. Build utilities are in
`scripts/`, optional diagnostics in `tools/`, checks in `tests/`, documentation in
`docs/`, and specifications in `tickets/`. Only launchers/configuration and
repository entry documents remain at the root. The existing `criclytics/` folder
is an ignored local virtual environment, not application source.

The19public pages include new workspace and scouting views. Existing URLs are
retained with documented API validation/statistical migrations and new versioned
endpoints. Legacy heuristic predictions stay withdrawn, rather than serving
invented probabilities. Original artifacts are not silently rewritten.
Public static files use `/static/`; checkout/data/config files are not served.

## Checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q criclytics_app scripts tools app.py wsgi.py
# Optional: install tools/browser-requirements.txt and a browser, then:
python -m tools.browser_audit
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
on offline tests and dependency scanning. Credential/production verification,
remote release controls and human/prospective gates still block release; see
[the runbook](docs/OPERATIONS_RUNBOOK.md). Existing resources are preserved: do not
activate billing or assume a new free compute Space is available. Source/free-tier
feasibility is recorded in [LIVE_FEASIBILITY.md](docs/LIVE_FEASIBILITY.md).
Nothing has been deployed from the local ticket branches.

## Data and limitations

Historical data is from [Cricsheet](https://cricsheet.org/), under its published
licensing terms. Live integrations exist for CricAPI/Cricbuzz and rankings, but
availability, rights, quotas and timely next-delivery coverage need revalidation.
Do not describe this subset of matches as a player's complete official career.
The project has no paid-service or credit-card budget. Full source/cost gates and
honest fallback modes are part of the roadmap.
