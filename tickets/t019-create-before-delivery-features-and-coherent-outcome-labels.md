# T019: Create before-delivery features and coherent outcome labels

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T018
- Branch: work/t019-before-delivery-features
- Base: T018 3bb3805

## Problem

Yearly-average labels/full-career features do not represent next-delivery outcomes and introduce leakage.

## Scope

Define next-attempt versus next-legal-ball product and coherent joint/factorized labels for batter runs/extras/total/dismissal. Build shared replay/serving features for score/target/phase, partnership, form and smoothed matchup history. Start with male T20I and explicit sparse/cold-start priors.

## Acceptance criteria

- [x] All features exclude target delivery and future innings/matches
- [x] Wicket can coexist with extras/runs without contradictory labels
- [x] Same pipeline produces replay/live feature vectors and documents missingness
- [x] Chronological match-grouped train/calibration/test partitions and leakage checks exist

## Validation

Hand-calculated vectors, future-data perturbation/cutoff tests, rare/illegal delivery labels and deterministic snapshot hashes.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Next-attempt product includes illegal deliveries and coherent exact runs/extras/dismissal labels. Shared numeric vector accepts only prior state/announced IDs/strictly earlier completed-day history. Generator updates only after yielding target row; same-day and overlapping match history are isolated. Cold priors remain null until empirical previous data exists; smoothing uses20 prior attempts, not fabricated probabilities. Export is streamed/private under a SQLite read snapshot with logical-source and row hashes. Historical timestamps remain unknown: retrospective order tests do not prove prospective source availability. Rollback retains isolated store/export and leaves default serving unchanged.

### Session update 2026-10-28T12:35:56+00:00

Chained from T018 3bb3805. Shared next-attempt features use source IDs, only prior attempts and strictly earlier completed-date history; same-day matches stay isolated. Joint outcome labels preserve simultaneous runs/extras/dismissals; historical source-availability uncertainty stays explicit.

### Session update 2026-10-28T12:40:54+00:00

56tests55pass/one optional skip. Shared pre-attempt vectors and exact joint labels pass hand vectors, target/future-match perturbation, cutoff, same-day grouping and multi-day overlap tests. Two100match exports reproduce23,104rows and identical SHA256; train58matches/13426rows, calibration21/4826, test21/4852, chronological cutoffs recorded. Null target/schedule/cold priors remain missing; publication availability remains unknown. See FEATURES.md and audit/features-2026-10-28.json. No model/prediction claim or deployment.
