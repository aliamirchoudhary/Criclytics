# T019: Create before-delivery features and coherent outcome labels

- Status: Planned
- Priority: P1
- Depends on: T018
- Branch: feat/t019-create-before-delivery-features-and-coherent-outcome-labels
- Base: latest dev

## Problem

Yearly-average labels/full-career features do not represent next-delivery outcomes and introduce leakage.

## Scope

Define next-attempt versus next-legal-ball product and coherent joint/factorized labels for batter runs/extras/total/dismissal. Build shared replay/serving features for score/target/phase, partnership, form and smoothed matchup history. Start with male T20I and explicit sparse/cold-start priors.

## Acceptance criteria

- [ ] All features exclude target delivery and future innings/matches
- [ ] Wicket can coexist with extras/runs without contradictory labels
- [ ] Same pipeline produces replay/live feature vectors and documents missingness
- [ ] Chronological match-grouped train/calibration/test partitions and leakage checks exist

## Validation

Hand-calculated vectors, future-data perturbation/cutoff tests, rare/illegal delivery labels and deterministic snapshot hashes.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
