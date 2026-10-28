# T023: Support attributed fielding and incident annotations

- Status: Implemented; real review pending
- Priority: P2
- Depends on: T018,T019
- Branch: work/t023-fielding-annotations
- Base: T022 f270c63

## Problem

Dropped catches misfields and on-field incidents are not consistently present in source data.

## Scope

Define attributed manual/imported annotations with delivery ID, observer/source, event/recorded time, confidence, review/revision state and access scope. Protect private tactical notes separately. Use unknown values where no reliable observation exists.

## Acceptance criteria

- [x] Missing annotation never means no incident/drop
- [x] Backfilled observations are excluded from earlier forecasts
- [x] Conflicting/corrected observations retain provenance/revisions
- [x] Replay consumes eligible annotations deterministically and works without them

## Validation

Ordering/revision/missingness/access fixtures and a small reviewed manually annotated match example.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Immutable private-ledger fielding/incident revisions and deterministic prior-attempt context implemented. Exact payload allowlist excludes tactical notes; public/owner scopes and conflicting sources are explicit. Missing occurrence/actor is unknown, not false. Grouping by attempt/type/chance avoids double counting unknown versus identified fielder. Backfilled availability/current-target guards and historical revision cutoffs are tested. Example is explicitly authored fiction; actual reviewed match/video rights and efficacy remain unavailable and no incident features are promoted. Local ingestion time is separate from trusted imported source-observed claims; future live ingress must own capture timestamps. Rollback retains observations/ledger and disables optional consumption.

### Session update 2026-10-28T13:07:16+00:00

Chained from T022 f270c63. Add source/observer/review/access-scoped manual fielding and incident revisions to local ledger. Missing is unknown; backfilled/current-target observations cannot enter earlier forecasts. No real dropped-catch evidence is invented.

### Session update 2026-10-28T13:12:18+00:00

68tests67pass/one optional skip; latest annotation/context targeted6tests pass. Fielding/incident records retain observer/source/event/source-observed/local-ingested/review/access/revision provenance. Missing/no-coverage remains unknown, explicit reviewed false differs, current/future/backfilled observations excluded from earlier contexts. Conflicting sources and actor uncertainty retained without double counting; tactical text rejected into separate workflow. Authored3record fictional example replays reverse/duplicate input deterministically; no real coach/video review or predictive benefit claimed. See ANNOTATIONS.md/audit/annotations-2026-10-28.json; no model feature enabled.
