# T048: Fresh-context model training and evaluation

- Status: Planned
- Depends on: T042,T047
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Freeze a fresh untouched chronological cohort before fitting; train CPU baselines/tabular candidates with exact state and supported source families; calibrated joint probabilities, ordinal/continuation and match-result targets evaluated separately.

## Acceptance and verification

Baselines, calibration, whole-match uncertainty, form/identity cold starts, subgroups, context ablations, runtime age and CPU memory; retain losing candidates and stable old artifacts.

## Limits and handoff

No auto-promotion from retrain success; T034/T039 test cohorts never retuned.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
