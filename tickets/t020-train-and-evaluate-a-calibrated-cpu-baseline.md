# T020: Train and evaluate a calibrated CPU baseline

- Status: Planned
- Priority: P1
- Depends on: T019,T014
- Branch: feat/t020-train-and-evaluate-a-calibrated-cpu-baseline
- Base: latest dev

## Problem

There is no valid next-delivery model or out-of-time calibration evidence; old pickles have no trusted contract.

## Scope

Compare empirical/smoothed baselines with simple reproducible CPU classifiers using match-grouped temporal splits, training-only preprocessing and separate calibration/test periods. Store trusted artifact hashes/schema/environment/seed/data manifest, model card and per-model scalers. Do not load arbitrary uploaded pickle.

## Acceptance criteria

- [ ] Report log loss Brier calibration rare-event/subgroup/coverage results versus predeclared baselines
- [ ] Test period stays untouched during feature/model selection; match-clustered uncertainty reported
- [ ] Cold-start/missing data uses documented priors or abstention without fake confidence
- [ ] Artifact schema/version checks and measured CPU runtime/memory satisfy budget

## Validation

Reproducible subset training, leakage audit, finite/coherent probability tests, artifact roundtrip and latency/memory benchmark. Promotion requires measured evidence, not training accuracy.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
