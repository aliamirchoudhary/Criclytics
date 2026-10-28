# Prospective shadow protocol v1 — frozen before collection

Registered2026-10-28T17:31:35Z, on the T030 local branch before implementation
and before any prospective cohort collection. No prospective results exist.
Code/tests will use clearly authored fixtures only. This protocol cannot turn the
already inspected2016–2018/T022 historical samples into prospective evidence.

Population: first30enrolled complete men's international T20I matches, regular
innings, six-ball overs, using permitted local manual scoring only. Replay is
reported separately and never counted as live success. Enrolment, source-rights
declaration, independent timing-review method/reviewer/evidence reference and
the frozen protocol hash must precede that match's first issued forecast/attempt.
If human timestamp evidence cannot establish the actual attempt's start, it is
unscorable prospectively. The collector capture time is not ball-start proof.
Source delivery coverage outside the collected archive is unknown, never100%.

Freeze learner `fe917b696bb25d2672b94f68e590fd665cdeed21ec06c55e23bafc1dda319beb`,
feature_schema1 and the T019 training-export hash in that artifact. No retraining,
test-driven threshold tuning or context addition. Build empirical additive-one
joint counts and phase/innings shrinkage20 baselines from **training rows only**,
with the same label vocabulary/OTHER. Record their artifact hash before enrolment
and issue both baseline distributions with each learner forecast from the same
pre-attempt core. Absence of a pre-issued baseline is a counted failure; never
retrofit a baseline into an old ledger entry.

Choose the **first originally issued** forecast for each physical target attempt,
including correction-linked replacements; never choose the most successful
revision. Require its model/baseline/protocol identity, state/feature hash, source
cutoff and issue time. Require issue time strictly before both independently
reviewed actual attempt start and original source observation, and after protocol/
enrolment/source-cutoff. Equal, late, unknown, mismatched or replay timing fails.
Evaluate against latest adjudicated canonical outcome, but preserve first outcome
receipt/timing and count corrections. Conflicting actual-start revisions fail
timing review. Missing forecasts/observations/unknown timestamps/abstentions and
late entries remain in denominators and reason counts.

Metrics: joint log loss, multiclass Brier,10-bin top-label ECE/calibration bins,
OTHER/unseen outcomes, dismissal/illegal/phase/innings/cold-history subgroups with
sample counts, source observation lag, revisions/corrections, missingness and
coverage. Match-cluster bootstrap200, seed17, learner-minus-each-baseline log-loss
intervals. Compare observed outcome frequencies to the training label prior as
descriptive drift, not a universal pass test. Missing subgroup/event evidence is
null with a reason, not zero error. JSON metrics never contain NaN/Infinity.

Promotion requires all30matches and at least5,000eligible scored attempts,
collected-attempt forecast coverage>=90%, reviewed timing>=95%, no known late
entry counted as eligible, source-lag p95<=5seconds, and learner log-loss delta
95%upper<0 against **both** frozen baselines. ECE<=0.03 and supported rare-event
subgroups need at least100dismissal and100illegal attempts; sparse groups prevent
promotion. These thresholds are preregistered operational targets, not scientific
guarantees. Full source coverage, coach safety/usefulness, rights/$0 and release
security gates still require independent review. Passing arithmetic alone cannot
automatically release an artifact; a human review is mandatory.

Weather, XI/pitch/home, fielding and media/crowd families remain excluded from the
production model. Their prospective benefit is null. Any future family requires
a separate preregistration, its own as-issued availability/coverage proof, fixed
model pair and a fresh cohort; existing inspected test matches cannot be reused
as a fresh confirmatory test. No paid API/LLM/GPU, billing or source bypass.

Current decision: NO-GO / prospective cohort pending. No claim of validated live
accuracy, measured coach adoption or a completed prospective ablation. T030's
tooling can be reviewed locally while this external evidence remains pending.
