# T020 predeclared CPU baseline protocol

Frozen before model fit/test outcome inspection,2026-10-28. Input is the T019
100match/23,104row export with rows SHA256
5bed4be60ad00a9fb6078d5547487b4858d318b38f01d43698857eb7f9868aa0.
Keep its58train/21calibration/21test whole-match chronology and date groups.
No random holdout or tuning on test outcomes. Source publication times are unknown,
so this is retrospective order validation, not prospective source-availability proof.

Compare three fixed models: (1) training-only empirical joint counts with additive
one smoothing and reserved OTHER outcome; (2) training-only phase/innings counts
shrunk with20 pseudo-attempts toward model1; (3) multiclass L2 logistic regression,
C=1, lbfgs, max_iter1000, tol1e-6, seed17, one CPU thread. All T019 numeric features
are allowed, excluding participant identifiers/date/label fields. Numeric nulls
become0 with a separate missingness mask. Standardization mean/scale are fit on
training rows only. No feature/hyperparameter search or test-driven selection.
OTHER captures exact joint outcomes unseen in training; its mass remains explicit,
not converted into invented batter/wicket marginals. Model3 receives the empirical
OTHER mass and scales known-class probabilities to the remaining mass.

Fit one temperature for model3 by minimizing joint calibration-period log loss,
bounded0.5?5 (fixed before fit). Never fit on test. Models1/2 remain uncalibrated
references. The preselected experimental artifact is model3 even if it loses to
a baseline; a loss blocks promotion instead of causing post-test retuning. Export
numeric JSON weights/scaler/schema/seed/environment and hashes, not a pickle.

Report held-out joint log loss, multiclass Brier and10-bin top-label ECE/reliability,
including rare-event and innings/phase/cold-history subgroups, row/match coverage,
unseen-outcome mass and sample limitations. ECE is diagnostic, not a calibration
certificate. Bootstrap200 samples of whole test matches with seed17 for95% interval
of loss difference against global baseline. No per-ball independence assumption.
Report CPU fit/roundtrip inference time and local resident memory. Repeat the fit
with unchanged data/protocol to check artifact identity; runtime samples may differ.

No promotion:100 file-selected2016?2018 matches are small/stale and not representative
of current cricket; feature publication availability and prospective replay/live
parity remain unknown. Public prediction facade stays unavailable. Trusted artifact
loading requires an externally supplied expected SHA256, supported schema/feature
versions, finite dimensions and coherent joint labels. Unknown/cold histories use
training-derived priors/missingness or abstain, never an invented50% or confidence.

The classifier/calibration APIs follow official documentation and the installed
pinned versions: [scikit-learn logistic regression](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.LogisticRegression.html),
[calibration guidance](https://scikit-learn.org/1.8/modules/calibration.html),
[SciPy scalar minimization](https://docs.scipy.org/doc/scipy-1.17.1/reference/generated/scipy.optimize.minimize_scalar.html).

## Numerical convergence amendment before test evaluation

The first fit hit1000iterations and raised ConvergenceWarning as a hard failure,
before writing model.json or materializing/evaluating test rows. Increase only
the optimization iteration ceiling to5000, retaining objective/C/solver/tolerance,
features, splits, seed and calibration bounds. This is a recorded solver-budget
change based on training convergence, not test metrics or model selection. The
failed run is build/t020-fit-first.log; its partial model directory does not exist.
