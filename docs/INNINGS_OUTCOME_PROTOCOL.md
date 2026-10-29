# T039 preregistered terminal-score and match-result candidates

Freeze in a local commit before fitting or inspecting these target results.
Experimental CPU-only candidates, no promotion or change to issued next-ball
records. The T034 date cohort has already been examined for a different target;
this is a new-target retrospective evaluation, not independent prospective proof.
Do not retune after examining this report or claim fresh unseen collection dates.

Population: existing male international six-ball T20I single-date corpus through
2026-10-29. Require two regular innings and an explicit winner or tied result;
exclude no-result/abandoned matches without those labels. Supers excluded from
player scores. Sort whole matches/date;60/20/20whole-date train/calibration/test.
All rows from a match stay together. Record exclusions, dates, counts and hashes.

Player target: observed terminal batter runs in that regular innings, conditional
on being the striker for at least one attempt. Extract one entry row immediately
BEFORE that player's first striker attempt from the ordered delivery sequence.
Known entry context: source player/bowler IDs, venue, bowling team, innings, phase
(first6/next9/rest overs), and wickets already lost (0-2/3-5/6+). Labels are fixed
bins0,1-9,10-19,20-29,30-49,50-74,75-99,100+. All later batter runs form the label,
never an input. Not-outs/chases/shortened innings are observed terminal scores,
NOT latent runs had play continued. Do not censor them away or extrapolate a
survival curve. Players run out without ever striking are outside this estimand.
Retain not-out share as descriptive coverage. No claim of pre-match participation
or of an exact future score, an in-progress continuation model or a survival model.

Match target: one joint canonical sorted-team outcome, teamAwin/teamBwin/tie.
Use winner when explicitly present, otherwise tied regular-innings result; ignore
eliminator winner for the latter estimand. Never fit two independent contradictory
win percentages. Venue/teams only; no final score, toss, result-derived team rank
or later innings information is an input. This is a hypothetical pre-match result
candidate; actual pre-match publication times remain unavailable in historical JSON.

Player components: global, entry phase/innings/wicket bucket, player, first bowler,
venue, opposition and player last5prior entered innings. Smoothing strengths:
0/20/40/80/80/80/10. Match components: global, canonical teamA, canonical teamB,
exact rivalry, venue, teamAform, teamBform; strengths0/40/40/30/80/10/10. Team
recent form records last5prior results in each team's own win/loss/tie perspective;
reverse teamB form into canonical output space. Defer all same-date history updates.
Frozen tables use train ONLY. Calibration/test history may advance only after
completed earlier dates. Global additive smoothing1per fixed label.

For each target, learn7nonnegative mixture weights on calibration log loss by EM,
uniform start, one pseudocount/weight, max200/tolerance1e-8; then fit one temperature
on calibration only, bounds0.5..3. Retain both preselected candidates regardless of
test performance. No hyperparameter/feature search or replacement of target bins.

Report joint log loss, multiclass Brier,10-bin top-label calibration error,
200whole-match bootstrap loss differences versus global and entry/rivalry reference.
Also report coherent50+/100+ binary Brier/calibration from the SAME score-bin
distribution, cold player/team coverage, rows/matches, data dates, weights and
temperature. Intervals quantify retrospective sampling uncertainty, not guaranteed
future accuracy. Report both winners and losers; do not select by held-out outcome.
Export bounded private numeric JSON, reports/hashes and one normalized distribution
per target. No pickle, public weights, external inference, billing or live rollout.

Next steps require independent review, prospective data and separate continuation/
sequence simulation validation. Weather, home/crowd, captaincy, injuries, psychology,
unannounced XI and politics remain unsupported rather than invented coefficients.
