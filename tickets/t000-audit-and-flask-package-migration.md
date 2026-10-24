# T000: Audit and Flask package migration

- Status: Implemented, awaiting review
- Priority: P0
- Depends on: None
- Branch: chore/audit-and-flask-structure
- Base: latest dev

## Problem

The checkout mixes public files and private source/configuration.

## Scope

Establish factory, blueprints, restricted assets, anchored paths, build/deployment boundaries and documented audit. Preserve existing API analytics during migration.

## Acceptance criteria

- [ ] 17 pages and all 30 API routes are preserved; local assets resolve
- [ ] Private config/source/Git/data paths return 404 and bootstrap cannot close script tags
- [ ] Twelve captured offline API responses match the old snapshot
- [ ] Original reports/data are preserved and audit/roadmap/tickets/branch policy exist

## Validation

Run the offline suite, opted-in local-data regression, compile Python, check JS syntax, build artifacts and review browser evidence. This is the current branch; not deployed.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

See docs/VERIFICATION.md and migration tests; awaiting review.
