# T022: Add lineup matchup and pitch-context feature families

- Status: Implemented; experimental context gated
- Priority: P2
- Depends on: T017,T019,T020
- Branch: work/t022-lineup-matchup-context
- Base: T021 c429067

## Problem

XI roles and pitch descriptions are not reliable structured model inputs; tracking/bounce data is absent.

## Scope

Record timestamped announced XI/substitutions/roles and sourced pitch/ball-condition reports. Add smoothed matchup history and explicit home/away venue context. Separate inferred tendencies from measured tracking, and evaluate each family independently.

## Acceptance criteria

- [x] Late/substituted XI and reports are gated by publication time
- [x] Sparse matchup estimates shrink to priors and show sample size
- [x] Pitch proxies have source/confidence and never invent line/length/bounce
- [x] Held-out family ablations decide inclusion rather than plausibility

## Validation

Late-XI/substitution/alias fixtures, sparse-matchup tests and chronological feature-family comparisons.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Local immutable as-of context ledger and deterministic announced-lineup/substitution/pitch/home helpers implemented. Stable IDs required; source/observer/quality/timestamps retained. Measured tracking requires explicit instrument/method; reported tags are not bounce measurements. New independent chronological matchup experiment follows protocol committed before fitting; no reuse/tuning on T020 test results. Matchup history retains empirical shrinkage/sample counts and remains experimental. No eligible published XI/pitch/home context exists in historical sample, so those families remain absent and their benefit is not invented. Rollback preserves ledger/experimental exports; public model/dataset unchanged.

### Session update 2026-10-28T12:59:13+00:00

Chained from T021 c429067. Timestamped lineup/substitution/pitch/home context contracts; no retrospective XI/pitch facts assumed available. New matchup ablation uses previously unevaluated2019?2021 source window and fresh date-grouped holdout, not the peeked T020 test period.

### Session update 2026-10-28T13:05:54+00:00

65tests64pass/one optional skip. Immutable UTC context ledger covers announced XI/substitutions/roles, sourced pitch-quality/tracking and explicit home affiliation; future/unknown records abstain. Sparse source-ID matchup estimates shrink with sample counts. Preregistered e050a22 independent2019?2021 window:100matches/22306attempts,65/21/14whole-match splits. New held-outlogloss1.8947full vs1.9535without matchup; match-cluster delta-0.0588,95%[-0.1218,-0.0043], small14match limitation. XI/pitch/home families have0eligible records and stay excluded. No model promotion or external calls. See MATCH_CONTEXT.md/audit/context-ablation-2026-10-28.json.
