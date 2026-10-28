# T010: Add golden cricket fixtures and data-schema contracts

- Status: Implemented; local review pending
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

### Session update 2026-10-28T09:42:59+00:00

Branch chained from85b50ab. Portable fictional CC0 golden fixtures, deterministic ETL/API contracts, strict ingestion codes and honest diagnostic implemented. Both Python3.11/3.12 tests pass (latest3.12:40tests39pass/one optionalskip). Initial full schema audit exposed80 legacy miscount strings and8 penalty-key mismatches; narrow audited normalization and actual pre/post keys fixed, golden regressions added. Final v2.0.1 full rebuild in build/data-v2-schema-final running; no serving artifact promoted. H2H single-format record/query orientation and callers migrated together. Diagnostic failure exit1 verified.

### Session update 2026-10-28T09:44:51+00:00

Five CC0 fictional hand-verified golden matches cover separate Test innings/milestones, extras/BF/legal balls, non-striker runout, retired hurt/out/timed out, draw/tie/no-result, super overs, pre/post penalties and maiden credit. Strict versioned ingestion rejects unknown structural/scoring fields and malformed types with code/location; corrupt inputs quarantined before aggregation. Full audit found80 legitimate legacy miscount string files (90events), explicitly normalized/audited;8 actual pre/post penalty cases corrected. v2.0.1 candidate build/data-v2-schema-final accepts6651/6651 zero rejects, all output/pipeline hashes verified, original artifacts unchanged. Evidence docs/audit/schema-corpus-2026-10-28.json and aggregation-v2-schema-2026-10-28.json; initial88-case findings retained separately. Repeated golden rebuilds deterministically equal; semantic player/H2H/venue/list/detail API tests pass. Single-format H2H returns a record oriented to caller order, format spellings/callers migrated. Diagnostic checks statuses/contracts and exits1 onfailure; actual failure exit verified. Python3.12 suite40tests39pass/one optionalskip, Python3.11 previous39-test suite38pass/oneskip; latest golden5/5pass; compile/changedJS checks pass. DATA_SCHEMAS.md documents opaque non-scoring metadata/unsupported over lengths and scope. No deployment/data promotion.
