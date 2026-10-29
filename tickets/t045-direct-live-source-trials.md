# T045: Direct live source and schedule discovery trials

- Status: Planned
- Depends on: T025,T026,T038
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Compare actual direct permitted API/HTML/browser sources, source rights/robots, no-card limits, scheduled match discovery and windows. Implement an adapter only with a documented basis; one producer and global budget.

## Acceptance and verification

Independently observed issue-before-ball timing, p50/p95 lag, actors/illegal balls/gaps/corrections and no per-user fetch; failed source trials retained.

## Limits and handoff

No Google Search scraping, stealth, restricted endpoints or fake timing proof. External blocker may remain.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
