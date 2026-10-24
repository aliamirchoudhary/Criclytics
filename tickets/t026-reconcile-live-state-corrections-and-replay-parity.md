# T026: Reconcile live state corrections and replay parity

- Status: Planned
- Priority: P1
- Depends on: T018,T019,T025
- Branch: feat/t026-reconcile-live-state-corrections-and-replay-parity
- Base: latest dev

## Problem

Provider ordering/corrections/IDs are not reconciled; invalid or stale state could generate forecasts.

## Scope

Route raw observations through canonical reducer with dedup/order/correction handling, historical/provider mappings, revisions and source lag. Invalidate next-delivery derived state when necessary; handle innings end rain target changes reconnect and abandonment.

## Acceptance criteria

- [ ] Duplicate/out-of-order/corrected events converge without double counting
- [ ] Recorded live/replay state and feature vectors agree
- [ ] Stale incomplete contradictory state blocks forecasts with reason
- [ ] Original issued forecasts remain immutable while replacements reference new revision

## Validation

Correction/drop/reconnect/target-revision sequence tests and recorded allowed live-to-replay parity.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
