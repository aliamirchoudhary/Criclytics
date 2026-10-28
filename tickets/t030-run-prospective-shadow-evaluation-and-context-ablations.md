# T030: Run prospective shadow evaluation and context ablations

- Status: Tooling implemented; prospective cohort pending
- Priority: P1
- Depends on: T020,T027,T028
- Branch: feat/t030-run-prospective-shadow-evaluation-and-context-ablations
- Base: latest dev

## Problem

Backtesting alone cannot validate real-time forecast quality or benefits of additional context.

## Scope

Freeze model/baselines/evaluation protocol, collect permitted matches with issue cutoffs, align outcomes to original forecasts/revisions and report lag/coverage/abstention/calibration/subgroup drift. Label replay versus prospective evidence; compare context families with the frozen baseline.

## Acceptance criteria

- [x] No forecast issued after outcome is counted as live success
- [ ] Log loss Brier calibration rare-event/subgroup and match-clustered uncertainty are reported
- [x] Lag/correction/missingness failures are counted instead of filtered away
- [x] Predeclared promotion criteria decide release or return to data/model work

## Validation

Immutable ledger/timestamp audit, independently replayed metrics, alignment spot checks and held-out ablation reports.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Audit machinery verified on authored fixtures; actual prospective metrics/cohort remain pending and the metrics acceptance item stays open.

### Session update 2026-10-28T17:31:35+00:00

Chained from T029 98408cf. Freeze prospective protocol before new scoring/tooling. No actual future cohort exists; implement immutable timing/adjudication tooling and report pending/no-go without inventing performance.

### Session update 2026-10-28T17:44:50+00:00

Protocol frozen in0e3b5b0 before implementation/collection; trusted training-only baseline artifact461043fd133601034a0a4421a7d43a0edf7c3a0f92ba0f428e08abfa30c65213; optional new pre-issued baselines/protocol IDs, no retrofitting old entries. Bounded idempotent decision ledger; reader fast path fixes measured logging regression (first repeat p95~110ms failed; final~74ms passes local100ms target, max~221ms, one inference/input). Auditor selects original first issue, strict actual/original observation/enrolment cutoffs, raw receipt/revision/feature replay and numeric probability reproduction; late/unknown/missing/corrections retained.89tests88pass/one optional skip; latest audit3tests pass; actual workspace browser regression passes. Authored virtual-clock fixture only:1scored/3collected,1late,1missing,1corrected,1unknown actual start. ACTUAL prospective cohort0: metricsnull/NO-GO, optional context benefitnull. SHADOW_EVALUATION.md and separate real-pending/fixture/resource/artifact reports. Actual30match/5000attempt cohort, independent physical timing and human review remain external; no deployment/promotion/push.
