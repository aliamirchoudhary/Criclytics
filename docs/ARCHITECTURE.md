# Architecture and migration

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

## Intended evolution

1. Repair security, statistical summaries and UI truthfulness.
2. Add explicit data/source manifests, IDs, event schemas and replay.
3. Build one tested CPU baseline for next-delivery outcomes using only information
   available before the delivery; begin with T20 internationals.
4. Prove permitted live access, timestamps and correction handling, then deploy
   inference in shadow mode. Keep manual/replay modes when live access fails.
5. Add independently measured context features and coach workflows.

Use SQLite for local transactional metadata/event indexes and partitioned
columnar artifacts for offline training only after workload measurements justify
them. A hosted SQL database, Redis dependency, message broker, microservices,
Kubernetes, GPU or paid feature store is not a prerequisite.

## T006 repository and refresh ownership

Each factory instance owns a bounded (32-file) JSON repository. A generation is
keyed by resolved path, nanosecond mtime and byte size. Parsing/index building
completes before publication under a lock. Invalid replacements retain last-good
objects. Mutation is isolated through defensive copies; historical details use an
ID index and lists/search receive compact projections, never the full snapshot.
Raw-match caching is app-owned too. Producers must publish changed generations
with atomic replacement; in-place edits retaining size and mtime are unsupported.

Live cache v1 stores explicit Unix `written_at` with payload, atomically replaces
disk JSON and mirrors an expiring namespaced Redis entry. Disk always retains
stale fallback. Legacy plain JSON uses disk mtime; legacy Redis TTL alone is
unknown freshness and is ignored. API callers still receive unwrapped payloads.
At most 128 new JSON keys can be admitted per live directory; existing files/data
are preserved. Public unknown IDs cannot trigger provider detail refreshes.

A SQLite provider-wide lease/backoff row in LIVE_DIR serializes refreshes across
workers sharing that volume; it expires after a crash. No per-ID lock dictionary
or paid Redis is required. Without a shared disk, configure exactly one collector
and disable HTTP refresh in other replicas; these are not distributed leases
across unrelated hosts. Provider daily-budget reservation/scorecard scheduling is
T025; live fetch stays disabled by default. Legacy CLI writers still need their
T007/T025 migration and must not run concurrently with serving until migrated.

Offline measured warm list/detail: 347/8.49 ms, one processed parse; resident
working set ~250 MB with engine disabled. Cold list ~3.12 seconds. These are local
Windows samples, not hosted capacity guarantees; evidence is in audit/repositories-
2026-10-28.json. Keep initial deployment to one worker until measured on its host.

## T009 scoring candidate

pipeline/scoring.py is the shared per-innings scorer for raw detail and rebuilds;
pipeline/aggregation.py fills summary tables from explicit innings identities.
`python -m criclytics_app.pipeline.cricsheet --output <fresh-directory>` delegates
to streaming rebuild.py. It never chooses data/processed as implicit output.
The full verified local candidate is build/data-v2-final (ignored data); serving
continues to select the existing processed artifacts until schema/migration review.
See SCORING_CONTRACT.md and audit/aggregation-v2-2026-10-28.json for deliberate
statistical changes. There is no automatic production data promotion.

json_io.py centralizes atomic publication and shared-delete Windows readers;
bounded retry handles transient Windows sharing failures. Linux uses normal
file handles with atomic rename. A failed write leaves the old artifact intact.

T010 supersedes the T009 development candidate with build/data-v2-schema-final
(schema2.0.1), correcting actual pre/post penalty keys and recording90 narrow
miscount-count normalization events across80 source files. Strict ingestion checks
all6,651 inputs, with zero rejects; original sources/processed artifacts stay intact.
Portable golden fixtures and DATA_SCHEMAS.md define the tested boundary. None of
these ignored candidates is selected for production automatically.

## T011 public UI

All17 allowlisted templates load application.js/application.css, using safe DOM construction and shared accessible navigation/forms/tables. Original markup is archived in docs/history/ui-pre-t011, outside static deployment output. The shared renderer owns these pages; legacy page scripts remain as historical assets and are not loaded by the new templates. Runtime API configuration and removal/consolidation of legacy assets remain T012. No dataset promotion or deployment accompanies this UI change. See UI_ACCEPTANCE.md.

## T012 frontend ownership

`frontend.py` validates a public origin and generates runtime configuration for
both Flask and the dependency-free static builder. The shared runtime loads
runtime-config.js, dom.js, api-client.js and application.js; the later scouting
page additionally loads coaching.js for its local private-plan workflow. The API helper
coalesces in-flight GETs, bounds requests to15 seconds, retains no completed
response/error cache and sends no credentials. Filter generations reject late
results; application initialization is idempotent. Match detail now always uses
the same API path on Flask/static hosting; server bootstrap has been retired
from page delivery. Legacy scripts/styles remain compatibility assets, unloaded.
Active styles are self-contained with system fonts; no third-party font/icon
load is required. Script/attribute CSP is enforced, with no inline allowances.
See audit/frontend-runtime-2026-10-28.json for request and synthetic preview checks.

## T014 diagnostics

App-owned fixed counters and256 request samples live in services/diagnostics.py.
/api/health is liveness; /api/ready and /api/status check required artifact roots
and report optional cached-feed degradation separately. Repository inspection
recognizes malformed replacement generations despite retaining last-good data.
Request logs use generated IDs and endpoint names, never raw URLs or bodies.
Offline tools.diagnostics measures local memory/payload/latency with live access
disabled. See DIAGNOSTICS.md for limits and the public status contract migration.

## T015 immutable datasets

Rebuilds emit manifest version1 plus coverage/source licence metadata and a
deterministic dataset identity. pipeline.artifacts validates JSON allowlist,
hashes, schema roots and inventory accounting, then retains immutable versions
and selects one via atomic pointer under a local SQLite promotion lock. Optional
DATASET_STORE pins the validated selection at app startup; legacy data remains
selected when unset. /api/coverage and UI expose only public coverage metadata.
Publication availability is unknown, distinct from the latest match-date cutoff.
See DATASETS.md and pipeline/source_registry.json for rights, retention and restore.

## T016 collection gate

Dated integrations/live_source_policy.json selects historical replay/local manual
mode only. Existing refresh/CLI primitives require source_policy approval before
network calls; environment flags/keys alone do not grant it. Current network
allowlist is empty. Real feed lag/coverage/corrections remain unmeasured.
LIVE_FEASIBILITY.md records primary terms, no-card/quota decisions and synthetic
experiments, including current restrictions on creating new HF compute Spaces.
Preserve existing resources; do not assume a new free Docker backend is available.

## T017 stable identity registry

Offline pipeline.identities binds source/register IDs and alias sets to one dataset.
Optional IDENTITY_REGISTRY is validated against dataset_id at startup. Identity
metadata APIs and selected profile/list/summary IDs coexist with legacy name URLs;
ambiguous names return409. Name-keyed multi-label aggregates are not silently
combined. Explicit reviewed match maps deduplicate canonical identity while
retaining original IDs/source references; unknown joins stay separate. See
IDENTITIES.md for provisional venue/team IDs, observed memberships and limits.

## T018 delivery observations and replay

Offline pipeline.events imports bounded validated historical subsets into private
SQLite observations/receipts and indexed immutable event revisions. Replay tracks
score/legal-ball/innings/partnership state with source IDs, explicit penalties
and observed target controls. Latest and as-of views differ; unknown historical
availability is never replaced with import time. DELIVERY_EVENTS.md describes
strike/target abstention and correction/reorder rules. No HTTP ingest is enabled.

## T019 feature contract

Shared pipeline.features.vector builds pre-attempt numeric values from replay state,
announced participant IDs and strictly previous completed-date history. Joint
labels permit simultaneous runs/extras/dismissals. Same-day matches share no final
history; chronological match/date-grouped partitions reject boundary overlap.
Private JSONL exports are streamed under one SQLite snapshot with deterministic
row/source hashes. Missing target/schedule/priors stay null, and retrospective
source-availability uncertainty remains explicit. See FEATURES.md.

## T020 experimental CPU model

ml.baseline compares fixed smoothed empirical/context counts with train-only
standardized logistic regression and separate temperature calibration. Portable
JSON inference requires an externally trusted SHA256 and strict feature/schema/
finite-weight/joint-label checks; no pickle loading. OTHER is explicit unknown
outcome mass. MODEL_CARD.md records held-out metrics and no-go promotion: the
small/stale historical sample and unknown source availability do not support
current coaching forecasts. Legacy prediction availability remains false.

## T021 optional weather

services.weather validates explicit venue/UTC/issue/validity/observation provenance
and selects only eligible as-of fields in a bounded local cache. Reanalysis,
future issue/observation and unknown location/cutoff abstain. No collector or
model weather inputs are enabled; sample weather coverage is zero. WEATHER.md
records primary free-service rights, candidate traffic limits and exclusion.

## T022 timestamped match context

services.match_context stores immutable local context revisions and selects only
published/observed/effective records at cutoff with explicit ownership. XI and
substitutions use stable IDs; pitch quality is separated from measured tracking;
venue affiliation is explicit. Unavailable families remain excluded from modelv1.
A separately preregistered future-window matchup ablation is recorded in
MATCH_CONTEXT.md; no experimental model is promoted. Event subset import can
filter explicit date windows while retaining source integrity checks.

## T023 annotations

Context ledger also stores attributed fielding/incident revisions, with local
ingestion time separated from claimed source times. services.annotations resolves
only earlier attempts, keeps conflicts/unknown coverage explicit and prevents
actor uncertainty from double counting a chance. Tactical text is excluded from
annotation payloads and private owner scope remains local, not HTTP auth. No
annotation model feature is enabled; ANNOTATIONS.md records fictional evidence
and the pending real reviewed observation/prospective validation gates.

## T024 optional proxy research

MEDIA_RESEARCH_PROTOCOL.md preregisters bounded observable media/crowd research,
not psychological ground truth. tools.media_research validates authored-fixture
rights/availability/identity windows and agreement arithmetic. Real agreement and
benefit remain unknown; no collector, paid model or production proxy is enabled.
This P3 exclusion does not block core historical/manual/replay workflows.

## T025 local collection adapter

integrations.collector is a bounded manual/replay-only CLI/library with same-volume
SQLite leases, shared quotas/receipts/kill state and immutable EventStore writes.
Capture time is worker-owned; read_snapshot uses read-only SQLite and cannot
collect. Source errors/backoff/quota/stale/kill flags block inference while
preserving last-good display. No public write endpoint or hosted worker is added;
LOCAL_COLLECTOR.md records limits and pending human/prospective evidence.

## T026 reconciliation and immutable derived history

services.reconciliation reads raw workspace stores at a confirmed source cutoff,
reuses reducer/vector and caches16source receipt/revision cores. StateLedger stores
immutable snapshots/forecasts with separate invalidation/replacement links; old
readers cannot regress current source state. Explicit innings ending, target/
schedule and appended metadata revisions preserve earlier views. Online contexts
require actual ingestion by cutoff. RECONCILIATION.md records strict abstention,
replay emulation limits and no external live/model-promotion claim. T017A is the
explicit required follow-up for discovered name-keyed aggregate collisions.

## T017A identity-based player summaries

pipeline.player_id_stats scores source-ID substituted raw matches into a separate
SQLite candidate with a parent-dataset/registry/database hash manifest. Optional
IDENTITY_PLAYER_STORE enables read-only bounded player/profile/search/comparison/
ranking/record/venue-player queries; default artifacts remain selected otherwise.
Aliases resolve uniquely or409, and observed memberships never imply nationality.
See PLAYER_ID_AGGREGATES.md for the explicit compatibility and rollback contract.

## T027 local shadow forecasting

services.forecasts binds trusted numeric model/evaluation hashes to the shared
Reconciler core and StateLedger. Default-off api.forecasts exposes versioned
loopback/same-origin state/forecast/history reads with explicit experimental
semantics. Collector reservations serialize source confirmation; readers never
collect. Unsupported/stale/ended state abstains; current-state/model issuance is
idempotent and correction-linked. Public prediction availability stays false.
FORECAST_API.md documents configuration, timing uncertainty and rollback.

## T028 workspace UI

The18th allowlisted page workspace.html uses the shared renderer and versioned
forecast/history API. Explicit manual/replay/unavailable modes, confirmation
expiry without polling, source/model/context coverage and immutable issued anchors
keep historical distributions distinct from current eligibility. WORKSPACE_UI.md
records local setup, browser evidence and remaining validation limits.

## T029 scouting and local private plans

api.scouting/services.scouting use only the bound identity player store, with an
optional offline bounded source-ID delivery evidence JSON. The19th page scouting
uses coaching.js for descriptive preparation and page-memory private plans with
explicit file export/import. No private input reaches server storage or URLs and
no hosted ownership guarantee is claimed. COACH_SCOUTING.md separates archive
coverage, scenario assumptions, data loss/export behavior and pending real feedback.

## T030 prospective audit machinery

ml.shadow_baselines freezes training-only empirical/phase artifacts for optional
pre-issued comparisons. ml.shadow_evaluation audits first issues against raw
receipt/feature replay and reviewed actual timing, retaining missing/late/correction
failures and null unknowns. StateLedger also keeps bounded idempotent decisions;
repeated current issued reads avoid write transactions. SHADOW_EVALUATION.md
separates authored fixture validation from the empty real cohort and NO-GO gate.

## T031 independent readiness preparation

tools.release_preflight builds clean allowlisted artifacts and runs offline API/
containment smoke plus isolated SQLite/dataset restore fixtures. It never deploys
or approves release. OPERATIONS_RUNBOOK.md records the real coach pilot protocol,
incident/backup/rollback procedures, $0 constraints and unmet T001/T013/T029/T030/
Git-publication gates. Actual pilot/prospective counts stay zero and release blocked.
