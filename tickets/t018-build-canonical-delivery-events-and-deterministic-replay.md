# T018: Build canonical delivery events and deterministic replay

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T010,T015,T017
- Branch: work/t018-delivery-replay
- Base: T017 85b7371

## Problem

Summary JSON discards delivery state required for labels training and live correction handling.

## Scope

Define immutable raw observations and versioned canonical delivery attempts with innings/attempt/legal-ball identities, striker/non-striker/bowler, runs/extras/wickets, source hashes and event/observed times. Preserve revisions and use bounded local indexed storage plus replay reducer.

## Acceptance criteria

- [x] Replay rebuilds score strike legal balls wickets targets and innings transitions
- [x] Illegal balls multiple dismissals super overs rain revisions and corrections have explicit rules
- [x] Duplicate/reordered input is idempotent while original observations remain auditable
- [x] Unavailable historical timestamp precision is recorded as unknown

## Validation

Golden sequence/conservation tests, reorder/duplicate/correction replay and reconciliation with corrected ETL aggregates.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Immutable observations/receipts and canonical versioned attempts use private indexed SQLite storage. Source-ID players prevent name aggregation collisions from contaminating events. Reordered/duplicate data is deterministic; conflicting immutable revisions fail and corrected/tombstoned attempts replay downstream state. As-of queries exclude future revisions, with unknown historical availability explicitly separated from prospective use. Strike after wickets/crossing ambiguity and unavailable Test/super-over targets abstain rather than invent state. Rain targets require observed ordered revision controls; no DLS approximation. Rollback: unselect this isolated store and retain original observations/previous artifacts; importer never overwrites.

### Session update 2026-10-28T12:27:53+00:00

Chained from T017 85b7371. Source-ID delivery attempts, immutable observations/revisions and SQLite replay; historical precise event/publication times stay null. Derived chase targets/strike inference will explicitly distinguish unknown revisions and wicket/crossing ambiguity.

### Session update 2026-10-28T12:34:10+00:00

53tests52pass/one optional skip. Five portable golden matches reconcile totals/wickets/legal balls, plus reorder/duplicate/correction/tombstone/strike/target/as-of checks. Fresh bounded historical maleT20I store imports100matches/23,104attempts; every match reconciles with corrected innings scorer and verified raw hashes, zero provider calls. Unknown historical timestamps stay null; source-observed and local ingestion times differ. Derived chase targets unverified and wicket/crossing ambiguity abstains. See DELIVERY_EVENTS.md and audit/delivery-replay-2026-10-28.json. No default-serving change, live parity or production deployment.
