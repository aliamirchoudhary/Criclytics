# Before-attempt features and labels v1

The product is **next attempted delivery**, including wides/no-balls. It is not
next legal ball, next over or a yearly performance milestone. Joint outcome labels
retain exact batter runs, each extras family, total runs, legal status and all
counted dismissal kinds. Runs/extras/wickets can coexist. Retired hurt/not out do
not count as a dismissal. A later classifier may reserve OTHER for unseen joint
outcomes; it cannot replace their mass with contradictory independent outputs.

`pipeline.features.vector` is shared by replay and future local serving. It reads
only state before the target attempt, announced participant IDs and already known
history. It has no access to target runs/extras/wickets. The generator yields a
feature row before updating state/history with its label. No yearly/full-career
aggregate tables, final outcomes, media narratives, inferred psychology or final
weather/pitch conditions enter features. Source IDs avoid the T017 name collisions.

Features include score, wickets, legal balls, attempts, partnership, fixed legal
ball phase bands, last six **attempts** runs/wickets, current batter runs/balls and
bowler legal balls, earlier batter/matchup sample counts and smoothed historical
batter runs/dismissal-attempt rates. The bowler history rate concerns a delivery
associated with that bowler, including run-outs; it is not credited bowling wickets.
The last-six/current-innings values are short-term descriptive form, not evidence
of pressure or a latent mental state. Same-day matches do not update each other's
prior-match history. Only matches completed on a strictly earlier calendar date
are merged, so overlapping/multi-day matches cannot leak final totals backwards.

Historical sample/publication times remain unknown. Announced striker/bowler IDs
are a retrospective pre-attempt reconstruction, not proof of source publication
availability. State transitions use prior attempts, but prospective data-lag parity
still requires T026/T030. Do not market retrospective leakage tests as a real-time
point-in-time audit. Match-date grouping conservatively isolates same-day events.

Missing values stay null: first-ball run rate, truly cold historical priors,
unverified chase targets and unknown scheduled balls. Smoothing strength20 uses
the empirical rate from strictly prior completed matches, never an invented50%.
Cold start with zero prior data is null plus sample count0. Verified observed target
controls may supply runs required; final rain-reduced limits/retrospective target
fields are not assumed known. balls_remaining is populated only when a prior
verified schedule is supplied. Fixed phase bands are not certified reduced-match
powerplay boundaries. Missingness masks/imputation must be fit on training only.

`python -m criclytics_app.pipeline.features --store <private-sqlite> --output <fresh-private-directory>`

Export streams JSONL under one SQLite read snapshot and hashes rows plus logical
source match/revision payloads. Manifest includes feature names/schema, source
dataset identity, attribution and partition cutoffs. Output is private, not static.
The split uses60%/20%/20% of distinct match-start days, keeps whole matches and
same-day groups together, and rejects multi-day overlap across boundaries unless
a future explicit embargo policy handles it. It is deterministic, not random.
Earlier calibration/test matches may update history for later matches as observed
online context; that does not authorize fitting model parameters on held-out data.

Tests verify hand-calculated pre-attempt state, missing/cold values, simultaneous
no-ball/runs/run-out labels, target/future-match perturbation invariance, unique
match partition assignment, same-day isolation and overlap rejection. The local
100match export is reproduced twice with identical row/source fingerprints; see
 audit/features-2026-10-28.json. This small2016?2018 slice is a pipeline experiment,
not a representative current-cricket benchmark or a coaching model. No forecast
service or default dataset changes accompany this ticket.
