# T005: Paginate compact match summaries and update callers

- Status: Planned
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
