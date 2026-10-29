# T049: History query and rivalry media desk

- Status: Planned
- Depends on: T042,T043
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Gold match/innings/spell indexes, filters/autocomplete, structured questions, rivalry dossiers, milestones and sourced export cards. Bounded local intent/entity parsing for natural-language convenience; distinguish descriptive/scenario/forecast answers.

## Acceptance and verification

Representative fan/anchor queries reproduce source totals and date cutoffs; pagination/query limits; ambiguous intent choices, no arbitrary SQL or paid LLM dependency.

## Limits and handoff

Coverage gaps explicit; no fabricated articles, drama or complete-career claims.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
