# T017: Introduce stable cricket identities and provider mappings

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T015
- Branch: work/t017-stable-identities
- Base: T016 a120570

## Problem

Names/provider IDs do not join aliases renamed venues team changes and duplicate real matches safely.

## Scope

Create stable player/team/venue/match IDs and versioned aliases/provider mappings using Cricsheet register where available. Preserve source IDs and historical membership; uncertain joins enter explicit review rather than fuzzy destructive merge.

## Acceptance criteria

- [x] Same-name people and known venue/player aliases do not collide
- [x] Uncertain joins remain unresolved with evidence
- [x] Provider/history duplicates are reconciled with audit trail
- [x] Name URLs remain resolvable while APIs gain stable IDs

## Validation

Alias/collision/transfer fixtures, reviewed cross-provider match examples and migration coverage report.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented locally with dataset-bound optional registry; review/integration pending. Stable source IDs and explicit alias sets prevent same-name destructive merges. Membership is observed team/date history, not nationality. Name URLs retain exact recorded-label access; stable identities spanning multiple labels abstain from silently combining legacy aggregate tables. Venue substring-first lookup retired; collisions return409. Exact reviewed provider links retain both source references and prefer completed historical summaries. Real provider/history overlap was not established in available caches, so actual links remain zero; portable fictional examples exercise reconciliation and conflict audit. Legacy name aggregates remain under review, with UI warning and ambiguous profile/comparison containment when registry is selected. Rollback: unselect optional registry/restart; preserve every prior data/identity artifact.

### Session update 2026-10-28T12:18:17+00:00

Chained from T016 a120570. Four explicitly licensed Cricsheet register CSVs downloaded once to ignored build/ (about1.4MiB total), hashes retained. Stable registry will bind to a validated dataset; collisions/uncertain provider joins remain unresolved, not fuzzy merged.

### Session update 2026-10-28T12:25:52+00:00

Full dataset-bound registry:5,125 rostered source-player IDs across5,090 roster labels;68 colliding source labels,111 total alias collisions,119 observed multi-team players;109 teams/440venues/6,651matches. Aggregate batting/bowling4,834 labels are a different coverage unit, not a canonical player count. Official-register venues136, provisional304; uncertain aliases remain unresolved.25cached provider rows reviewed offline have zero historical date overlap, so zero real match links invented. Fictional reviewed duplicate/conflict fixtures and real ambiguous/profile/comparison409 checks pass.51tests50pass/one optional skip. See IDENTITIES.md and audit/identity-migration-2026-10-28.json; registry build/identities-v1-final.json remains opt-in/private, no deployment.
