# T023: Support attributed fielding and incident annotations

- Status: Planned
- Priority: P2
- Depends on: T018,T019
- Branch: feat/t023-support-attributed-fielding-and-incident-annotations
- Base: latest dev

## Problem

Dropped catches misfields and on-field incidents are not consistently present in source data.

## Scope

Define attributed manual/imported annotations with delivery ID, observer/source, event/recorded time, confidence, review/revision state and access scope. Protect private tactical notes separately. Use unknown values where no reliable observation exists.

## Acceptance criteria

- [ ] Missing annotation never means no incident/drop
- [ ] Backfilled observations are excluded from earlier forecasts
- [ ] Conflicting/corrected observations retain provenance/revisions
- [ ] Replay consumes eligible annotations deterministically and works without them

## Validation

Ordering/revision/missingness/access fixtures and a small reviewed manually annotated match example.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
