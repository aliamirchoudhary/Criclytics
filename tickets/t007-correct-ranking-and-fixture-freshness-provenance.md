# T007: Correct ranking and fixture freshness/provenance

- Status: Implemented; local review pending
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

### Session update 2026-10-28T09:00:26+00:00

Ranking HTTP cache-only, including LIVE_FETCH_ENABLED mode; explicit bounded offline ranking-import CLI replaces automated scraping until rights review. Per-category partial merge preserves last-good rows and original timestamps. April fallback effective_date2026-04, fetched_at null, stale/fallback true; unknown fixtures never stamped now. Shared plain-text provenance notices show source/effective/fetched/stale on home/rankings/team pages; Chrome375 source-label checks pass with no page errors (other API data stubbed; external resources blocked). 28 tests:27pass/one optional skip; compilation and JS syntax pass. Sample calendar merge disabled; schedule provider failure retains existing data; atomic outputs and envelope-aware existing-reader migration. Existing caches untouched. Evidence docs/audit/provenance-ui-2026-10-28.json; imports and rollback documented docs/API_CONTRACT.md. Automated source rights/collector selection deferred T015/T016.
