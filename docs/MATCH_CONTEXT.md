# Timestamped lineup, matchup and pitch context

ContextLedger stores immutable local JSON revisions in private indexed SQLite.
Records identify match/kind/source/observer, published/observed/effective times,
revision and public/private owner scope. The latest revision known by a cutoff is
selected using the maximum of those times. Duplicates are idempotent; conflicting
same revisions or changed record ownership/identity fail. Raw/private values are
never logged and no public ingest/notes endpoint is added. Payloads are bounded16KiB,
10,000revisions per match and1,024selected records; exhaustion fails explicitly.

Announced lineups use11distinct stable player IDs and explicit roles. A roster in
a retrospective Cricsheet file is not proof of an announcement before a delivery.
Late substitutions affect context only after publication/observation/effectiveness;
conflicting or already-replaced players produce unavailable state. Names/aliases
must first resolve through T017; ambiguous labels do not pick an arbitrary player.
Source corrections retain earlier versions. Team appearances are not nationality.

Pitch reports distinguish observer_report, unverified and instrument_measured
quality. Reported tags such as dry/green are not tracking. Numeric bounce/line/length
requires an explicit instrument/method and bounded finite measurements; otherwise
tracking is null. Confidence here is provenance/observation quality, not calibrated
prediction confidence. Home/away/neutral affiliation must be explicitly sourced
for a stable venue/team and known by cutoff; location/name alone does not infer it.
No pitch-bounce, player psychology or causal coaching benefit is manufactured.

Sparse matchup history is already part of T019: source-ID batter/bowler samples,
with20pseudo-attempt shrinkage to the empirical strictly prior completed-match
rate. Cold history is null until prior data exists. Sample counts are retained;
a one-ball matchup is not presented as a reliable career tendency.

## Independent family experiment

Protocol e050a22 in CONTEXT_ABLATION_PROTOCOL.md was committed before fitting a new
eligible2019?2021 window, separate from T020's examined2016?2018 test period.
The100file-selected matches produce22,306attempts and65train/21calibration/14test
match groups. Full and matchup-removed models use identical fixed CPU training
and separate calibration. Removed columns are absent before preprocessing across
all partitions, rather than just erased at test time. No new hyperparameter search.

On the new held-out test, joint log loss is1.8947with matchup history versus1.9535
without. Whole-match bootstrap200/seed17 reports delta-0.0588,95%interval
[-0.1218,-0.0043]. This small14match result supports retaining the family for
further experimental evaluation; it does not prove global, current or causal
benefit. Baselines, Brier/calibration and model identities are retained in
 audit/context-ablation-2026-10-28.json. No model is promoted or silently swapped.

Announced XI, pitch/ball-condition and home/away families have0eligible as-issued
historical records, so they remain excluded and benefit estimates stay null.
No timestamps or apparent pitch measurements are backfilled from final files.
Collect properly attributed local manual observations for a fresh preregistered
experiment before inclusion. The current UI/default dataset and public legacy
prediction availability remain unchanged; rollback can unselect optional contexts
without deleting their provenance or replacing historical/model artifacts.
