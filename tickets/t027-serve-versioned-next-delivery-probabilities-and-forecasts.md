# T027: Serve versioned next-delivery probabilities and forecasts

- Status: Implemented, awaiting review
- Priority: P1
- Depends on: T020,T026,T014
- Branch: work/t027-versioned-forecasts
- Base: preceding local ticket branch (resumed-session user override)

## Problem

Current prediction endpoints lack validated state freshness training-serving parity and immutable issued forecasts.

## Scope

Expose a versioned delivery API using shared feature pipeline, trusted schema/model identity and explicit stale/missing/out-of-domain abstention. Persist issue time/state revision/cutoff/feature hash/model/data identity before observing the event; bound inference cost.

## Acceptance criteria

- [x] Only eligible pre-delivery state produces forecasts; ended innings are unavailable
- [x] Probabilities are finite/coherent with documented extras/wicket semantics
- [x] Forecast ledger is immutable idempotent and correction-aware
- [x] Measured inference latency/memory and feature parity satisfy documented local targets

## Validation

State/model/feature contract tests, replay equivalence, unknown actors/stale tests and CPU latency/load measurements.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented as local experimental shadow only; promotion/public forecast acceptance remains NO-GO per MODEL_CARD.md.

### Session update 2026-10-28T17:09:56+00:00

Chained from T017A ba6525a. Implement default-off local experimental shadow API with trusted model and immutable ledger, no promotion or public forecasting claim.

### Session update 2026-10-28T17:14:48+00:00

Default-off local-only experimental API v1: state/forecast/history, trusted model+evaluation+dataset/feature hashes, shared Reconciler features, source reservation serialization, strict scope/stale/end abstention and immutable idempotent correction-linked ledger. Public predictions remain unavailable; no promotion.84tests83pass/one optional skip; latest seven forecast/reconciliation tests pass; compilation passes. Local real-weight sample:0.6912ms inference,100reads/4threads p95~62.9ms,1inference/1collectorinput; evidence docs/audit/forecast-service-2026-10-28.json. Source confirmation cannot prove actual ball start; prospective timing remains T030. Loopback Host/peer and same-origin/cross-site checks; no collector/write/upload endpoint, no external calls. Docs FORECAST_API.md; no deployment/push.
