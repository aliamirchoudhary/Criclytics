# T031: Release measured coach pilot and operations runbook

- Status: Blocked; offline readiness verified
- Priority: P1
- Depends on: T001,T002,T003,T013,T014,T015,T028,T029,T030
- Branch: work/t031-release-readiness
- Base: preceding local ticket branch (resumed-session user override)

## Problem

Completed/deployed claims do not establish safe correct useful real-time coaching analytics.

## Scope

Run bounded coach/player pilot, verify required prior gates, publish honest source/data/model cards and limitations, exercise quota shutdown backup/restore/rollback, and prepare reviewed dev-to-main release. Exclude optional context research unless validated.

## Acceptance criteria

- [ ] No hidden release-blocking security or statistical defect
- [ ] Coach task success quality metrics freshness coverage and $0 limits have evidence
- [x] Operator can restore/rollback without public-source exposure
- [x] Release checklist incident runbook feedback path and scope exclusions are explicit

## Validation

End-to-end pilot acceptance, security/dependency scan, clean artifact smoke, restore/rollback drill and prospective evaluation review. Publish only when authorized; no world-best or guaranteed-outcome claims.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Independent local readiness/runbook/drills verified; actual coach pilot and public release are blocked, not completed. Hosted restore remains unverified.

### Session update 2026-10-28T17:45:13+00:00

Dependency gates T001/T013 operator work, T029 real coach feedback and T030 actual prospective cohort remain open. Prepare independent offline runbook/artifact/restore checks only; no pilot/public release/deployment or restricted Git operations.

### Session update 2026-10-28T17:57:05+00:00

Independent preparation only; actual pilot/release not started because T001/T013 operator gates, T029 real feedback and T030 prospective cohort remain open. Clean19page frontend/backend allowlists, offline API/readiness/CSP/private-path404 smoke,13original processed hashes unchanged, SQLite source+coordinator+issued-ledger backup/restore with kill/issued payload retained, two immutable dataset versions A->B->A rollback all pass.89tests88pass/one optional skip on BOTH Python3.11/3.12; compilation/activeJS checks pass; uv pip check both environments pass; current pinned31package audit0known advisories. Report docs/audit/release-preflight-2026-10-28.json, OPERATIONS_RUNBOOK.md, empty actual-pilot template; README current commands/limits corrected. No real coach participants/prospective matches, hosted restore, deployment URL, push/merge/remote repository mutation. Main ef7c279/dev e4f7ab4 unchanged. Publication/integration requires explicit later Git approval; HF upload also creates a restricted remote commit. Credentials/auth tasks deferred as requested; no repeated credential request.

Final configuration check also rejects using the raw source or collector-coordinator file as the derived forecast ledger. Both Python versions cover these rejection cases; the final Python3.12 full89-test suite passes with one optional skip.
