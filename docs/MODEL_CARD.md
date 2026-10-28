# Experimental next-attempt model card v1

**Not promoted. Public prediction availability remains false.** This historical
experiment does not establish valid current coaching, betting or live forecasts.
Model SHA256: `fe917b696bb25d2672b94f68e590fd665cdeed21ec06c55e23bafc1dda319beb`.
Weights are local ignored JSON, never an uploaded pickle. The expected SHA256 must
come from this reviewed release record, not an untrusted model's own metadata.

Data:100 deterministically file-selected maleT20I matches,2016?2018,23,104 attempts,
derived from Cricsheet JSON underODC-BY1.0. This is a small coverage slice, not full
careers or present-day cricket. Source dataset and exact feature hash/cutoffs are
in audit/cpu-baseline-2026-10-28.json.58training matches end2017-12-24;
21calibration matches start2017-12-29/end2018-03-10;21test matches start2018-03-12.
Same-day groups stay together. Historical publication/ball availability is unknown;
retrospective order checks are not prospective leakage/lag proof.

Protocol was committed before fit in d357306. The first fit failed convergence at
1000iterations before an artifact/test evaluation. Training-only amendment87bd2c6
raised the optimization ceiling to5000 without changing features/C/solver/tolerance,
partitions or calibration bounds. No test-driven tuning/selection followed.
Logistic regression uses L2/C1, lbfgs, seed17, one CPU thread; train-only numeric
scaling with zero/missingness mask, separate calibration-period temperature fit.
All T019 numeric inputs are included, never participant/date/label identifiers.
Reserved OTHER explicitly holds unseen joint outcomes and is not a physical runs
or wicket class.39known joint labels plus OTHER conserve probability mass. One
held-out attempt has an unseen exact joint outcome.

| Held-out model | Joint log loss | Multiclass Brier | Top-label ECE (10bins) |
|---|---:|---:|---:|
| Empirical additive-one joint prior | 1.7741 | 0.7547 | 0.0077 |
| Phase/innings counts, shrinkage20 | 1.7524 | 0.7421 | 0.0068 |
| Logistic + calibration temperature | 1.7547 | 0.7427 | 0.0154 |

Lower is better. The learner improves over the global prior but does not
demonstrate improvement over the stronger phase/innings baseline. Whole-match
bootstrap200/seed17 gives learner-global loss delta about-0.0194,95% interval
[-0.0309,-0.0091]; learner-phase delta about+0.0023, interval[-0.0106,+0.0140].
These21match intervals and ECE do not prove broad calibration or rare-event skill.
Report includes calibration bins, actual dismissal/illegal and phase/innings/cold
subgroups; subgroup rows/matches are shown to expose sparse coverage. There is no
97?99% accuracy or arbitrary confidence claim. OTHER prevents exact unqualified
wicket/runs marginals; do not treat unknown mass as zero-risk.

Two unchanged fits produce identical model hashes. Portable inference matches
scikit-learn probabilities before calibration and roundtrips trusted JSON. Tests
perturb only test labels and verify unchanged weights/preprocessing/calibration.
Unsupported schemas, wrong hashes, bad dimensions/non-finite weights/incoherent
labels and invalid feature input fail. Cold histories retain missingness and
training-derived priors; they do not invent50%. Unknown/unsupported input abstains.
Artifact environment/feature schema/seed/data identity accompany numeric weights.
No remote artifact download or arbitrary code deserialization is supported.

Local single-CPU fit/calibration/test-load sample was about22.2seconds, resident
about280MB, artifact29,879bytes, mean one-vector inference about0.27ms over100calls.
These are Windows local samples, not hosted capacity guarantees; no GPU, paid API,
LLM or billing activation was used. Source helpers preserve the $0/no-card gate.

Promotion remains NO-GO: small/stale selection, unknown historical publication
availability, unproven prospective parity, no measured coach pilot and no clear
improvement over the stronger baseline. T027 may expose only a clearly marked
experimental shadow distribution with explicit abstention, never silently enable
legacy endpoints or claim validated current forecasts. A new representative,
predeclared experiment and prospective evidence are required for production claims.
[Source attribution/licensing](https://cricsheet.org/licensing/).
