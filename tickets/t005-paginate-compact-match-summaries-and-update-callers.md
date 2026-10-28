# T005: Paginate compact match summaries and update callers

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T004
- Branch: fix/t005-paginate-compact-match-summaries-and-update-callers
- Base: latest dev

## Problem

The match list downloads about 43 MB of full scorecards and is requested repeatedly by several pages.

## Scope

Define compact server-side filtered/sorted summaries with bounded pagination; reserve enriched scorecards for detail endpoints. Update home/matches/search/recent-results callers together and reconcile known provider aliases.

## Acceptance criteria

- [ ] Default fixture listing is below a documented 250 KiB target
- [ ] Stable pagination has no gaps/duplicates for fixed snapshot
- [ ] Listing pages never download the full historical scorecard corpus
- [ ] Detail still returns complete scorecard; cold/warm payload/latency are measured

## Validation

Contract tests, full-data measurements and browser filters/navigation/pagination. Replace only deliberately changed legacy fingerprints with explained contracts.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:50:04+00:00

Compact filtered/sorted summary pagination and all known callers migrated together; detail scorecards preserved. 20 unit tests (19 passed, one optional legacy skip), Python compilation and JS syntax pass. Chrome 375/1440 pagination and empty-filter interactions pass with synthetic fixtures; external assets blocked. Full local corpus default payload 12,708 bytes below 250 KiB, 6,271 fixtures; cold/warm 2589.6/2078.34 ms. Evidence docs/audit/match-listing-2026-10-28.json. Exact-ID deduplication and explicit team aliases only; cross-provider identity matching deferred T017. Existing data untouched; T006 addresses parsing latency. Branch chained from work/t004-api-validation, per session override. Rollback requires paired API/frontend release.
