# T022: Add lineup matchup and pitch-context feature families

- Status: In progress; ablation protocol frozen
- Priority: P2
- Depends on: T017,T019,T020
- Branch: feat/t022-add-lineup-matchup-and-pitch-context-feature-families
- Base: latest dev

## Problem

XI roles and pitch descriptions are not reliable structured model inputs; tracking/bounce data is absent.

## Scope

Record timestamped announced XI/substitutions/roles and sourced pitch/ball-condition reports. Add smoothed matchup history and explicit home/away venue context. Separate inferred tendencies from measured tracking, and evaluate each family independently.

## Acceptance criteria

- [ ] Late/substituted XI and reports are gated by publication time
- [ ] Sparse matchup estimates shrink to priors and show sample size
- [ ] Pitch proxies have source/confidence and never invent line/length/bounce
- [ ] Held-out family ablations decide inclusion rather than plausibility

## Validation

Late-XI/substitution/alias fixtures, sparse-matchup tests and chronological feature-family comparisons.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T12:59:13+00:00

Chained from T021 c429067. Timestamped lineup/substitution/pitch/home context contracts; no retrospective XI/pitch facts assumed available. New matchup ablation uses previously unevaluated2019?2021 source window and fresh date-grouped holdout, not the peeked T020 test period.
