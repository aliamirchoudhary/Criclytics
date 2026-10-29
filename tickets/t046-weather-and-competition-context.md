# T046: Issued weather and competition context collection

- Status: Planned
- Depends on: T037,T043
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Version venue coordinates/home/neutral mappings, competition stage and attributed conditions; MET Norway conditional forecasts with identifying UA/Expires; optional qualifying Open-Meteo use only. Structured fielding/captaincy/crowd facts and rights references.

## Acceptance and verification

Same venue shared requests; forecasts retain issued/valid/received clocks; historical reanalysis cannot masquerade as issued; expiry/conflict/backfill/missing cases; no psychological label inferred.

## Limits and handoff

No causal rain/bounce adjustment without evaluated evidence; no news-body copying.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
