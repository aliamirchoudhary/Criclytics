# T007: Correct ranking and fixture freshness/provenance

- Status: Planned
- Priority: P1
- Depends on: T004,T006
- Branch: fix/t007-correct-ranking-and-fixture-freshness-provenance
- Base: latest dev

## Problem

Rankings can run long remote retry loops inside web requests; April 2026 fallback data is stamped with now.

## Scope

Move provider refresh to bounded explicit jobs/CLI. Separate effective date, fetched-at, source, fallback and stale state; label/remove sample calendars and preserve last-good categories on partial refresh.

## Acceptance criteria

- [ ] No ranking HTTP route launches scraping/sleeps
- [ ] Old fixture/ranking snapshots cannot appear freshly observed
- [ ] API/UI expose source date and stale/fallback status
- [ ] Partial empty provider response never destroys last-good categories silently

## Validation

Offline/stale/partial-refresh fixtures and browser labels for home/rankings/team profiles.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
