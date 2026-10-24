# T030: Run prospective shadow evaluation and context ablations

- Status: Planned
- Priority: P1
- Depends on: T020,T027,T028
- Branch: feat/t030-run-prospective-shadow-evaluation-and-context-ablations
- Base: latest dev

## Problem

Backtesting alone cannot validate real-time forecast quality or benefits of additional context.

## Scope

Freeze model/baselines/evaluation protocol, collect permitted matches with issue cutoffs, align outcomes to original forecasts/revisions and report lag/coverage/abstention/calibration/subgroup drift. Label replay versus prospective evidence; compare context families with the frozen baseline.

## Acceptance criteria

- [ ] No forecast issued after outcome is counted as live success
- [ ] Log loss Brier calibration rare-event/subgroup and match-clustered uncertainty are reported
- [ ] Lag/correction/missingness failures are counted instead of filtered away
- [ ] Predeclared promotion criteria decide release or return to data/model work

## Validation

Immutable ledger/timestamp audit, independently replayed metrics, alignment spot checks and held-out ablation reports.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
