# T022 context-family evaluation protocol

Freeze before importing/fitting/evaluating this experiment. Source window:
2019-01-01 through2021-12-31, first100 eligible maleT20I matches in deterministic
source-file order, bounded local import. No2016?2018 match from T020 is eligible.
Apply the same T019 whole-match/date-grouped60/20/20 chronological split. Use the
T020 fixed logistic training/calibration algorithm with amended5000iteration
ceiling; no hyperparameter search or test-driven tuning.

Fit a full-history model and one matchup-ablated model. In the ablation export,
prior_matchup_samples and prior_matchup_wicket_rate are null for every row before
any split preprocessing/fit; the same missing masks apply throughout. This makes
those columns constant/uninformative, not a test-time-only perturbation. Vocabulary,
scaling and parameters are fit on training only, temperatures on calibration only.
Compare untouched new test-period joint log loss/Brier/top-label calibration with
match-cluster uncertainty. No automatic production/model promotion; a weak or
uncertain difference retains exclusion/experimental status. No repeated selection
on the T020 test results is allowed.

Announced XI/substitutions/roles, sourced pitch reports and home/away affiliations
must pass published/observed/effective-time cutoffs. The raw corpus has no proven
announcement/report publication times, so those families remain absent and are
excluded without fabricated ablation scores. Matchups already have a measurable
source-ID/history contract; their inclusion still needs measured evidence. No
bounce/line/length, player psychology or causal coaching benefit is invented.
