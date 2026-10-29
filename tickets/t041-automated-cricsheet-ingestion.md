# T041: Automated authoritative Cricsheet ingestion

- Status: Planned; plan reviewed before implementation
- Depends on: T015,T016
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Daily bounded conditional downloads of the three supported official archives; immutable bronze hashes and exact snapshot extraction; validate every match; build and validate a complete three-format candidate; record source clocks/differences/withdrawals and preserve originals. Add read-only public-standard-runner schedule with no Git writes, upload or application/model promotion.

## Acceptance and verification

ZIP traversal/symlink/duplicate/expansion/schema tests; conditional304 and corrupt-cache recovery; full-archive removal semantics; failure keeps prior candidate; meaningful real source download and candidate build.

## Limits and handoff

Current branch feat/t041-automated-ingestion from36c6401. Hosted scheduling and durable delivery await approved integration/T042.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
