# T026: Reconcile live state corrections and replay parity

- Status: Implemented; replay parity verified
- Priority: P1
- Depends on: T018,T019,T025
- Branch: work/t026-reconcile-live-state
- Base: T025 fbd433e

## Problem

Provider ordering/corrections/IDs are not reconciled; invalid or stale state could generate forecasts.

## Scope

Route raw observations through canonical reducer with dedup/order/correction handling, historical/provider mappings, revisions and source lag. Invalidate next-delivery derived state when necessary; handle innings end rain target changes reconnect and abandonment.

## Acceptance criteria

- [x] Duplicate/out-of-order/corrected events converge without double counting
- [x] Recorded live/replay state and feature vectors agree
- [x] Stale incomplete contradictory state blocks forecasts with reason
- [x] Original issued forecasts remain immutable while replacements reference new revision

## Validation

Correction/drop/reconnect/target-revision sequence tests and recorded allowed live-to-replay parity.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Source-cutoff read-only reconciliation, bounded core caching and immutable derived/forecast-history ledger implemented. Unknown source lag stays null; critical incomplete/contradictory/stale/terminal state abstains. Explicit end/target/schedule/append-only metadata controls handle transitions; same physical event across observations preserves first canonical provenance. Source revision counters/lease checks prevent stale cached confirmations and older-reader regression. Shared vector parity is recorded historical replay, not a claim of external live proof. Rollback retains raw/revision/state/forecast ledgers and disables optional serving.

### Session update 2026-10-28T13:42:39+00:00

Chained from T025 fbd433e. Reconcile source revisions/declared next context through the shared reducer and vector; gaps/contradictions/stale/terminal/kill block forecasts. Preserve immutable derived state/invalidation history and explicit innings/target/schedule transition declarations; no external live feed claims.

### Session update 2026-10-28T14:13:23+00:00

80tests79pass/one optional skip. Recorded permitted historical replay verifies250pre-attempt vectors/final score and100cached readers with0rebuilds; actual live/provider/human SLA unproved. Gaps/reorder/semantic duplicates/corrections/tombstones, late reserved correction, score confirmations, terminal/stale/kill/quota, target/schedule/extra-innings metadata revisions and immutable state/forecast replacements tested. Online contexts require platform ingestion by cutoff. No public write route/model promotion/deployment. See RECONCILIATION.md/audit/stream-parity-2026-10-28.json. Added explicit T017A child for discovered name-keyed aggregate migration, required before T029.
