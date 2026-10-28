# T008: Contain misleading probabilities and validate legacy contracts

- Status: Implemented; local review pending
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

### Session update 2026-10-28T09:07:29+00:00

All unvalidated estimates withdrawn instead of partially correcting invalid heuristics. Preserved API URLs return explicit unavailable envelope with null probability/confidence/sample_count/cutoff, no model, empty leaderboards/evaluated_players0. Engine initialization lightweight/off by default; old formulas archived with construction blocked, never imported by serving. SC Cook/Test, missing data, all metrics, team/venue mismatched-schema containment and injected-engine isolation covered. No supported numeric estimator is claimed; monotonicity/schema/statistical validity gates apply on T020/T027 reintroduction. Removed invented compare percentages, H2H win forecasts, widget confidence/default50 and unsupported model copy. Fixed match-context initializer replacing historical insights panel. 30tests:29pass/one optional skip; Python and JS checks pass. 12 Chrome375/1440 cases across six surfaces pass, no page errors with other APIs unavailable and external assets blocked; evidence docs/audit/prediction-ui-2026-10-28.json. Prediction legacy fingerprints explicitly retired; docs/PREDICTION_STATUS.md describes scope/rollback.
