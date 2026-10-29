# T041: Automated authoritative Cricsheet ingestion

- Status: Implemented locally; durable publication/schedule activation pending
- Branch: feat/t041-automated-ingestion
- Plan freeze: 386ce44, before implementation
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

## Evidence - 2026-10-29

Full plan/double-check frozen in386ce44 before code. Implemented official-source
conditional ingestion, robots/rights checks, immutable bronze, exact authoritative
snapshots, schema/population/ZIP budgets, cross-process lease, corrected combined
candidate validation, changes/withdrawals and retained checkpoints. Added pinned
read-only public-standard-runner daily workflow; no Git/data upload/deploy/model
promotion. See docs/AUTOMATED_DATA_REFRESH.md.

Real build:7,150matches (897Test/2,607ODI/3,646T20I), latest2026-10-25, zero
rejected/excluded files, validated candidate093da9decbddfa72adf2d34dfe4dc0c2a6a0fbe10c73ebd5c0c081ae0ec37eb2.
Corrected real run~318seconds locally;13original processed hashes preserved.
Immediate rerun is not_due with zero network calls. A Windows Unicode progress
failure was fixed by capturing legacy stdout; failed partial output was never
selected. docs/audit/automated-refresh-t041-2026-10-29.json retains source hashes,
clocks, candidate identity and explicit limitations; raw archives remain ignored.

106unit tests105pass/one optional legacy skip. Focused tests cover304/unchanged,
corrupt-cache repair, removed matches, invalid-refresh last-good retention, unsafe
archives/expansion,429stop and competing lease. Compilation and workflow YAML/
public-only/read-only guards pass. No app JS/UI changed; owner preview preserved.

Hosted schedule is not activated and no running-site update occurred. T042 owns
durable free artifact delivery, combined identity/player marts, health and serving
activation after approved integration. Cricsheet is post-match history, not live
scoring. Old trained models remain unchanged; fresh training is T048.
