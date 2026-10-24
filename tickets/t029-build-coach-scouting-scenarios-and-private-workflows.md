# T029: Build coach scouting scenarios and private workflows

- Status: Planned
- Priority: P2
- Depends on: T010,T012,T017,T020,T023
- Branch: feat/t029-build-coach-scouting-scenarios-and-private-workflows
- Base: latest dev

## Problem

Generic profiles lack actionable preparation reports, transparent scenario assumptions and safe private notes.

## Scope

Implement focused opponent/bowler scouting with matchup/venue/phase/form evidence, sample sizes and attributed export. Add explicit what-if assumptions without causal claims. Private notes/rosters require tested ownership/session/CSRF and durable free storage; use local-only export if persistence cannot be guaranteed.

## Acceptance criteria

- [ ] Coach can prepare a plan and trace every statistic to source/cutoff/coverage
- [ ] Scenario changes expose assumptions/uncertainty rather than proven causal advantage
- [ ] Private data never leaks via public static/API; cross-user isolation tested if accounts exist
- [ ] Real coach feedback and ephemeral-storage loss/local-export behavior are documented

## Validation

Coach task walkthroughs, export/attribution tests, auth/CSRF/ownership tests when applicable and restore/export checks.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
