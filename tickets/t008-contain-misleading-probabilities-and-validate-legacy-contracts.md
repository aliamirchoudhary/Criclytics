# T008: Contain misleading probabilities and validate legacy contracts

- Status: Planned
- Priority: P0
- Depends on: T000,T004
- Branch: fix/t008-contain-misleading-probabilities-and-validate-legacy-contracts
- Base: latest dev

## Problem

Served heuristics are labelled trained ML; tails are reversed, confidence is fabricated, schema accesses mismatch and missing data becomes 50%.

## Scope

Remove unsupported accuracy claims and mark outputs unavailable or explicitly unvalidated. Establish inference envelope with kind/source/cutoff/sample count/unavailable reason. Correct schema/math only against reviewed invariants; no claim this is a next-ball model.

## Acceptance criteria

- [ ] Missing data has no invented probability
- [ ] Supported estimates obey P100 <= P50 and finite/unit/monotonicity rules
- [ ] UI distinguishes heuristics from saved models and removes arbitrary confidence
- [ ] H2H/team/venue nesting and leaderboard coverage are validated

## Validation

SC Cook/Test regression, synthetic math/schema/missingness invariants, browser unavailable states and explained retirement of changed legacy fingerprints.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
