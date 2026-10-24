# T017: Introduce stable cricket identities and provider mappings

- Status: Planned
- Priority: P1
- Depends on: T015
- Branch: feat/t017-introduce-stable-cricket-identities-and-provider-mappings
- Base: latest dev

## Problem

Names/provider IDs do not join aliases renamed venues team changes and duplicate real matches safely.

## Scope

Create stable player/team/venue/match IDs and versioned aliases/provider mappings using Cricsheet register where available. Preserve source IDs and historical membership; uncertain joins enter explicit review rather than fuzzy destructive merge.

## Acceptance criteria

- [ ] Same-name people and known venue/player aliases do not collide
- [ ] Uncertain joins remain unresolved with evidence
- [ ] Provider/history duplicates are reconciled with audit trail
- [ ] Name URLs remain resolvable while APIs gain stable IDs

## Validation

Alias/collision/transfer fixtures, reviewed cross-provider match examples and migration coverage report.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
