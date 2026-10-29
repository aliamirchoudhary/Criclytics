# T034 predeclared contextual candidate protocol

Freeze this protocol in a local commit BEFORE fitting or inspecting its held-out
results. Preserve T020 and all issued artifacts. This candidate is experimental.

Use the existing local male international six-ball T20I Cricsheet JSON corpus,
single-date regular innings only. Exclude super overs and multi-day availability
ambiguity. Sort whole matches by date then source ID; split dates60/20/20 percent
train/calibration/test, never split same-day matches across partitions. Missing
publication/actual delivery times remain unknown; this is retrospective validation.
Record corpus/file hashes, date coverage, exclusions and partition match/row counts.

Target is the existing coherent next-attempt joint label. Keep the63most frequent
training labels with count>=3, lexicographic tie break, plus reserved OTHER. Do not
inspect calibration/test outcomes to build vocabulary. Unknown labels map OTHER.

Fit conditional smoothed multinomial components: global, innings/phase, batter,
bowler, exact pair, exact observed venue name, team rivalry pair, batter recent
form and bowler recent form. No fuzzy identity joins. Phase: first6overs, next9,
remaining. Player/pair/venue/rivalry distributions shrink toward the training global
distribution with fixed strengths100/100/40/120/200; phase strength20, recent-form
strength50. Global additive smoothing1per class. Recent-form is the last5prior
completed matches' delivery outcomes by role; same-day observations are deferred.
During held-out evaluation earlier COMPLETED dates may update recent form, never
frozen global/player/pair/venue/rivalry model counts. Report this online-history
contract. No speculative mental state, crowd, rain or captaincy coefficient.

Learn9nonnegative mixture weights on calibration log loss with EM, uniform start,
one pseudo-count per weight, max200iterations/tolerance1e-8. Fit one temperature
on calibration only, bounded0.5–3, using scalar minimization. No test-driven choice
or retuning; export the preselected calibrated mixture even if it loses. Keep
global and phase distributions as test references. Only inference form snapshots
may advance through completed test dates; model counts/weights remain frozen.

Report test joint log loss, multiclass Brier,10-bin top-label ECE/reliability,
unknown-label share, sparse/cold coverage, learned weights, temperature, time/
memory and200whole-match bootstrap loss-delta intervals versus BOTH baselines.
No promotion unless independently reviewed prospective evidence supports it.

Bounded what-if inference uses exact known IDs, selected venue/teams, innings and
phase. Source/as-of date must not precede the artifact's latest form snapshot;
do not use a future snapshot to answer an earlier scenario. Expose component
sample sizes, shrinkage, model/form date scope, unknown mass and unsupported
context. Batter/bowler event views derive from one normalized joint distribution.
OTHER creates probability intervals, not invented exact wicket/six marginals.

Numeric JSON only, trusted externally configured SHA-256, bounded dimensions/
finite weights/counts, no pickle or user-supplied model paths. No live inference
integration or replacement of existing T027 models in this ticket.
