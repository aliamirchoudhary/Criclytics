# Local experimental next-attempt API v1

The public prediction facade remains unavailable. The historical CPU experiment
did not pass promotion gates; see MODEL_CARD.md. T027 exposes a **default-off,
loopback-only shadow workflow**, not validated current coaching predictions.
It never collects source data, uploads models, promotes an artifact or calls a
provider. HTTP source ingestion remains absent.

An explicit local configuration must supply `EXPERIMENTAL_FORECASTS=True`,
`WORKSPACE_SOURCE` (T025 private SQLite), a separate `WORKSPACE_LEDGER`,
`FORECAST_MODEL` and `FORECAST_MODEL_SHA256`, plus `FORECAST_EVALUATION` and
`FORECAST_EVALUATION_SHA256`. Hashes must come from reviewed local release
evidence, not an untrusted artifact's self-description. The model schema/weights,
evaluation model identity, source dataset and feature-export hash must agree.
All paths stay outside static output. No environment/settings are changed by
implementation. No live source or model is implicitly selected.

The reviewed local experiment uses private `build/baseline-v1-first/model.json`
and its `evaluation.json`. Actual hashes/latency evidence are recorded in
`audit/forecast-service-2026-10-28.json`; source/sample limits are in MODEL_CARD.md.
The artifact is numeric JSON, not pickle. The ledger must be backed up separately
from raw observations; retain immutable raw input and previous issued versions.

GET routes, where identifier is `match:manual:<id>` or `match:cricsheet:<id>`:

- `/api/v1/workspaces/<identifier>/state`: score/core, source cutoff/revision,
  lag (null when unknown), source age, context coverage and abstention reasons.
- `/api/v1/workspaces/<identifier>/forecast`: same state plus one immutable issued
  experimental forecast if eligible. Repeated state/model reads reuse its ID.
- `/api/v1/workspaces/<identifier>/history?limit=50`: issued entries, newest first,
  bounded1..200, including replacement links. Past entries are not current forecasts.

Responses are private/no-store. Disabled mode returns a structured unavailable
payload without creating a source/ledger or loading a model. When enabled, both
socket peer and Host must be loopback, Origin must be the same local origin when
present, and cross-site browser requests are rejected. Forwarded headers are not
trusted. Serve the local UI from the same local Flask origin. This is a single
operator local tool; it is not hosted authentication or private multi-user storage.

Only declared men's international T20I, six-ball overs, regular innings1/2 are
within this experimental model scope. Unknown participants, missing/contradictory
pre-attempt confirmation, gaps, pending correction, source kill/quota/error,
announcement older than15seconds, stale source older than60seconds, ended innings,
unsupported scope and changed state abstain. Cold histories remain null and are
labelled session-only: the service does not manufacture career priors. Weather,
XI/pitch/home and annotations are not enabled model features.

The service serializes against collector reservations on the existing local
coordinator database. Pending observations prevent inference; readers cannot
collect or consume source quota. It records the current shared feature core,
predicts with the trusted JSON artifact, rechecks eligibility and writes the
immutable state/model/feature/source-cutoff distribution before returning it.
The same local coordinator/ledger volume is required; this does not synchronize
unrelated hosts. Real play may start without an observation, so capture/confirmation
alone cannot prove a forecast preceded the actual ball. T030 must adjudicate
prospective timing; unknown actual ball time cannot be counted as proven pre-ball.

Each forecast contains issue time, target attempt, state ID, source revision hash,
source cutoff, feature hash/schema, model/data identity, coverage/cutoffs and source
mode. The target is the **next attempt including illegal deliveries**, not the next
legal ball. Probabilities cover coherent joint batter runs/extras/dismissals/legal
status plus explicit OTHER mass. OTHER's runs/wickets are unknown; no exact marginal
or zero-risk claim is derived from it. A correction creates a new state and a new
linked forecast; prior payloads remain immutable. Paused/stale/ended state returns
no current forecast even when older ledger entries exist.

Validation: portable model/hash/scope/ID/idempotency/correction/stale/privacy tests,
shared T026 parity, and a local real-weight100reader sample. One manual authored
session is not a prospective cohort or measured human scorer latency. Local targets
were one inference below10ms and four-reader p95 below100ms; these are diagnostic
checks, not hosted guarantees. No paid service, account mutation or deployment.

Rollback: disable `EXPERIMENTAL_FORECASTS` and restart. Retain source and derived
ledgers; old public unavailable behavior continues. No source/model migration is
required and no original artifact is overwritten.
