# T027: Serve versioned next-delivery probabilities and forecasts

- Status: Planned
- Priority: P1
- Depends on: T020,T026,T014
- Branch: feat/t027-serve-versioned-next-delivery-probabilities-and-forecasts
- Base: latest dev

## Problem

Current prediction endpoints lack validated state freshness training-serving parity and immutable issued forecasts.

## Scope

Expose a versioned delivery API using shared feature pipeline, trusted schema/model identity and explicit stale/missing/out-of-domain abstention. Persist issue time/state revision/cutoff/feature hash/model/data identity before observing the event; bound inference cost.

## Acceptance criteria

- [ ] Only eligible pre-delivery state produces forecasts; ended innings are unavailable
- [ ] Probabilities are finite/coherent with documented extras/wicket semantics
- [ ] Forecast ledger is immutable idempotent and correction-aware
- [ ] Measured inference latency/memory and feature parity satisfy documented local targets

## Validation

State/model/feature contract tests, replay equivalence, unknown actors/stale tests and CPU latency/load measurements.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
