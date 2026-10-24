# T018: Build canonical delivery events and deterministic replay

- Status: Planned
- Priority: P1
- Depends on: T010,T015,T017
- Branch: feat/t018-build-canonical-delivery-events-and-deterministic-replay
- Base: latest dev

## Problem

Summary JSON discards delivery state required for labels training and live correction handling.

## Scope

Define immutable raw observations and versioned canonical delivery attempts with innings/attempt/legal-ball identities, striker/non-striker/bowler, runs/extras/wickets, source hashes and event/observed times. Preserve revisions and use bounded local indexed storage plus replay reducer.

## Acceptance criteria

- [ ] Replay rebuilds score strike legal balls wickets targets and innings transitions
- [ ] Illegal balls multiple dismissals super overs rain revisions and corrections have explicit rules
- [ ] Duplicate/reordered input is idempotent while original observations remain auditable
- [ ] Unavailable historical timestamp precision is recorded as unknown

## Validation

Golden sequence/conservation tests, reorder/duplicate/correction replay and reconciliation with corrected ETL aggregates.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
