# Architecture and migration

Expanded platform design and reviewed execution order:
[CRICKET_PLATFORM_MASTER_PLAN.md](CRICKET_PLATFORM_MASTER_PLAN.md) and
[PLATFORM_PLAN_REVIEW.md](PLATFORM_PLAN_REVIEW.md). T041 adds the separate
source-to-candidate batch job documented in AUTOMATED_DATA_REFRESH.md; it does not
change application/model selection or create a durable hosted warehouse.

Current contextual candidate and serving additions: CONTEXTUAL_MODEL_CARD.md,
NEXT_BALL_PLATFORM_PLAN.md and PUBLIC_READ_CAPACITY.md. Full numeric models stay
private; scenario outputs remain experimental. Public historical responses use a
bounded per-worker LRU/singleflight layer; private/live/scenario data is excluded.

The current change establishes a Flask package and deployment boundary. It does
not replace Flask or the current UI with an unrelated stack. Blueprint extraction
preserves API behavior, and large legacy service/API modules are temporary seams
for subsequent tickets.

```text
app.py                         compatibility development launcher
wsgi.py                        production entry point
criclytics_app/
  __init__.py                  create_app, configuration, extensions, headers
  paths.py                     absolute checkout/package roots
  api/routes.py                existing /api contracts
  web/routes.py                allowlisted public page routes
  services/legacy.py           existing data/cache/scorecard helpers
  ml/probability.py            currently served heuristic engine (unvalidated)
  ml/training.py               legacy training/model loading (not served)
  pipeline/cricsheet.py        historical aggregation CLI
  pipeline/reference.py        curated metadata generator
  integrations/                live, schedule, matches, rankings, photos
  templates/                   17 HTML pages, existing *.html URLs retained
  static/css/                  shared stylesheet
  static/js/                   shared/per-page scripts
  static/images/               owned public images
data/                          existing raw, processed, live, static data
models/                        trusted local artifacts; not public web assets
scripts/                       safe frontend/backend build utilities
tools/                         optional diagnostics and browser audit
tests/                         offline checks and legacy response fingerprints
docs/                          current audit, architecture and product plan
docs/history/                  original reports/notes, preserved as historical
tickets/                       ordered implementation specifications
```

HTML files currently remain static documents in the templates directory, served
through explicit allowlisted routes. They are not yet a Jinja component system.
This preserves the same frontend artifact for static hosting. T012 can extract
shared components after UI behavior has regression coverage.

## Compatibility map

| Old location/command | New location/command |
|---|---|
| `python app.py` | Still works; `flask --app criclytics_app:create_app run` also works |
| `gunicorn app:app` | Compatibility still exists; use `gunicorn wsgi:app` |
| Root `*.html` | `criclytics_app/templates/`; page URLs unchanged |
| Root `*.js`, `styles.css`, PNGs | `criclytics_app/static/{js,css,images}/`; explicit redirects for known old asset names |
| `process_cricsheet.py` | `python -m criclytics_app.pipeline.cricsheet` |
| `create_static_files.py` | `python -m criclytics_app.pipeline.reference` |
| `ml_models.py` | `python -m criclytics_app.ml.training` |
| `ml_probability_engine.py` | `criclytics_app.ml.probability` |
| `fetch_live.py` | `python -m criclytics_app.integrations.live` (existing flags retained) |
| `fetch_schedule.py` | `python -m criclytics_app.integrations.schedule` |
| `scrape_matches.py` | `python -m criclytics_app.integrations.matches` |
| `scrape_rankings.py` | `python -m criclytics_app.integrations.rankings` |
| `fetch_photos.py` | `python -m criclytics_app.integrations.photos` |
| `debug_rapidapi.py`, verification/extraction scripts | `tools/`; diagnostics, not acceptance tests |
| `documentation/`, old data/UI audit notes | `docs/history/` |

Data/model files were not regenerated or moved. Default paths resolve relative
to the checkout, including ML defaults and CLI output paths. The existing root
data fallback is retained for old HF uploads; T015 replaces implicit discovery
with versioned artifact manifests. No source/config/data path is public just
because it exists in the checkout.

## Configuration

Copy `.env.example` to `.env`, keep real values out of Git, and set secrets in
the host's secret store. `LIVE_FETCH_ENABLED=0` is the default; cached/replay
operation must not consume provider quotas. Set it to `1` only after reviewing
the provider/account permissions and limits. Optional Redis is also disabled in
offline mode. CLI fetch commands explicitly request a fetch and can contact their
provider; do not run them merely to validate the structure.

`create_app(config)` accepts isolated `PROCESSED_DIR`, `RAW_DIR`, `LIVE_DIR`,
`REFERENCE_DIR`, credentials, CORS origins, and `INITIALIZE_ENGINE=False` for
lightweight tests. The current cache locks/backoff and raw-match cache still need
T006 to become safe across processes/app instances.

## Deployment and rollback

Backend: Docker starts `wsgi:app`, one worker/two threads initially. This is a
bounded default, not a measured capacity guarantee. `.dockerignore` excludes
secrets, Git, the local virtual environment, docs and raw match data. Processed
artifacts must already be provided separately; a clean clone does not contain
ignored datasets. The HF workflow stages a whitelist into `build/backend` and
uploads that directory only. It does not delete existing remote large data.
Provider secrets are never staged. Existing remote files must be reviewed during
the operator release ticket, including possible previously uploaded secrets.

Frontend: `python -m scripts.build_frontend` emits public pages and `/static/`
under `dist/`; `wrangler.jsonc` points at it and includes the direct CLI build
hook. Workers Builds also needs its dashboard Build command set explicitly to
that Python command; it currently ignores Wrangler Custom Builds. See the exact
[Cloudflare settings](CLOUDFLARE_DEPLOYMENT.md). Do not serve or upload the source
checkout as static content. Remote account settings have not been changed here.
T012 uses explicit FRONTEND_API_BASE public configuration (empty means same-origin).
Static builds must configure their HTTPS backend and corresponding CORS origin.

Both staging commands require a clean output directory, so an old unexpected
file cannot silently survive into a public release. Use a clean checkout/build
directory or `build_frontend --output` with a fresh external directory. Inspect
and remove only known generated output when rebuilding; never remove source/data.

Validate the backend/page/API contracts and static output before promoting a
release. Retain the last known-good release artifact and data manifest. Roll back
the release as a unit, preserving data; do not use destructive checkout resets.
Do not roll back to the vulnerable root static-serving configuration on a public
host. A tested restore drill and remote branch protections are T013/T031 work.
