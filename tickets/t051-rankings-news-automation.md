# T051: Category-aware ranking and factual-news jobs

- Status: Planned
- Depends on: T036,T042,T043
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Acquire a documented public reuse basis for ranking/news source adapters; weekly player/event-driven team ranking checks with atomic backups, drift validation and effective dates. News links/metadata/factual events only within verified terms.

## Acceptance and verification

Updated/unchanged/unavailable/partial categories retain provenance; no fresh timestamp for stale backup; published source/attribution, request budgets and automation health.

## Limits and handoff

Do not treat another site copying ICC as permission; monthly refresh is insufficient for current player rankings.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
