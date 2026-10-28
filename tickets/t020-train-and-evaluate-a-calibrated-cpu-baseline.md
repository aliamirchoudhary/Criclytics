# T020: Train and evaluate a calibrated CPU baseline

- Status: Implemented; experimental not promoted
- Priority: P1
- Depends on: T019,T014
- Branch: work/t020-cpu-baseline
- Base: T019 e47a364

## Problem

There is no valid next-delivery model or out-of-time calibration evidence; old pickles have no trusted contract.

## Scope

Compare empirical/smoothed baselines with simple reproducible CPU classifiers using match-grouped temporal splits, training-only preprocessing and separate calibration/test periods. Store trusted artifact hashes/schema/environment/seed/data manifest, model card and per-model scalers. Do not load arbitrary uploaded pickle.

## Acceptance criteria

- [x] Report log loss Brier calibration rare-event/subgroup/coverage results versus predeclared baselines
- [x] Test period stays untouched during feature/model selection; match-clustered uncertainty reported
- [x] Cold-start/missing data uses documented priors or abstention without fake confidence
- [x] Artifact schema/version checks and measured CPU runtime/memory satisfy budget

## Validation

Reproducible subset training, leakage audit, finite/coherent probability tests, artifact roundtrip and latency/memory benchmark. Promotion requires measured evidence, not training accuracy.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Experimental CPU training/evaluation implemented, review pending. Empirical/phase baselines and fixed logistic learner use whole-match temporal train/calibration/test periods and train-only preprocessing/vocabulary; separate temperature fit excludes test outcomes. Trusted numeric JSON avoids pickle; expected SHA256/schema/dimensions/coherent labels required. OTHER mass remains explicit for unseen joint outcomes. Learner does not establish improvement over the stronger phase baseline, so no promotion/current coaching claim. Historical publication availability is unknown and sample is stale/small. Rollback retains all artifacts and leaves legacy prediction endpoints unavailable.

### Session update 2026-10-28T12:42:24+00:00

Chained from T019 e47a364. Predeclared CPU protocol in docs/BASELINE_PROTOCOL.md committed before training/test outcome inspection. Existing100match chronological export; no hyperparameter or model selection on test. Public prediction facade remains unavailable.

### Session update 2026-10-28T12:51:48+00:00

60tests59pass/one optional skip. Protocol frozen in d357306, training-only convergence amendment87bd2c6; first1000iteration fit failed before test evaluation. Two5000ceiling fits produce identical trusted JSON hashfe917b696bb25d2672b94f68e590fd665cdeed21ec06c55e23bafc1dda319beb. Held-out21matches/4852attempts log loss: global1.7741, phase1.7524, calibratedlogistic1.7547; classifier not demonstrably better than phase baseline. Match-cluster intervals, rare/subgroup/coverage and calibration bins reported. Local~22s/~280MB/0.27ms inference; wrong hash/schema/nonfinite/coherence tests and test-label perturbation pass. MODEL_CARD.md documents NO-GO promotion; public prediction facade unchanged/unavailable.
