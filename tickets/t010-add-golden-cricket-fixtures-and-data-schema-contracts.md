# T010: Add golden cricket fixtures and data-schema contracts

- Status: Planned
- Priority: P1
- Depends on: T004,T009
- Branch: fix/t010-add-golden-cricket-fixtures-and-data-schema-contracts
- Base: latest dev

## Problem

The old verification script prints success after failures; statistical rules have no independent semantic regression suite.

## Scope

Add small licence-attributed hand-verified fixtures, ingestion validators and deterministic ETL/API tests. Replace misleading diagnostic success banners with assertions and nonzero failure status.

## Acceptance criteria

- [ ] Offline CI runs without ignored full datasets or provider accounts
- [ ] Fixtures cover extras/dismissals/innings/draw/tie/no-result/super-over distinctions
- [ ] Unknown/malformed fields are rejected/quarantined with a reason
- [ ] Same valid input yields deterministic equivalent outputs

## Validation

Golden rule and endpoint fixtures, corrupted data tests, repeated seeded runs and source/expected-value review.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
