# T042: Durable zero-cost publication and scheduler health

- Status: Planned
- Depends on: T041
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Verify an existing no-card durable artifact channel and exact quota/rights; publish validated combined data plus identity/player stores atomically with trusted manifests; retained previous version and restore; expose actual pipeline check/source/data/serving ages. Register scheduler health and missed-run detection.

## Acceptance and verification

Read-only consumer swaps one complete version; corrupt/missing/expired job retains last good; crash/restore and storage quota tests; actual hosted trial after release approval.

## Limits and handoff

Actions cache/artifacts are not durable storage; no new service/card or repository mutation without authorization.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
