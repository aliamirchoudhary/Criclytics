# T047: Exact-state feature registry and online parity

- Status: Planned
- Depends on: T034,T043
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Add legal attempts/score/wickets/target/required rate/partnership/batting order/recent sequence, role-specific recency and competition proxies. Share definitions across training/replay/runtime with source/age/units/missingness contract.

## Acceptance and verification

Known scoring golden fixtures, correction replay, before-attempt leakage, train/runtime feature hashes and format-specific targets; actual missing source fields abstain.

## Limits and handoff

Optional unsupported emotion/weather families cannot silently alter output.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
