# Separate terminal-score and match-result research (T039)

Protocol frozen in f70e8e9 before fitting/inspecting these target results. Private
numeric models are under ignored build/innings-outcomes-v1-full; no next-ball
model/issued ledger was replaced. Training/evaluation took50seconds on local CPU.
The two model files total about435KB. No paid inference or GPU dependency.

Population:3,174eligible men's international six-ball T20I matches,2005-02-17
through2026-04-09. Five multi-date and75incomplete/no-result matches excluded.
Whole-date train/calibration/test:1,593/758/823matches. Test begins2024-10-10.
This date cohort was examined for another target in T034; it is not independent
prospective validation. Actual historical publication/participant confirmation
timestamps remain unknown. Full results/hashes:
[evaluation](audit/innings-outcomes-t039-2026-10-29.json).

Player target uses an ordered sequence to capture the state immediately before
the batter's first striker attempt. It forecasts observed terminal runs in bins,
not runs had play continued or an in-progress survival curve. One row per entered
batter/innings; no future scores/wickets are input. Not-outs/chases/shortened play
remain observed terminal results. Players who never strike are outside scope.
Form uses last5prior entered innings, with same-date updates deferred. There are
25,417training,12,563calibration and13,618test player rows;2,705test not-outs.

| Player terminal-score metric | Global | Entry-state | Candidate |
|---|---:|---:|---:|
| Log loss | 1.64973 | 1.55324 | 1.55291 |
| Multiclass Brier | 0.75932 | 0.73246 | 0.73196 |
| Top-label10-bin calibration error | 0.02060 | 0.01931 | 0.00933 |

Difference versus entry-state is-0.000324 with95%whole-match bootstrap interval
[-0.001209,0.000767]. No clear additional log-loss advantage. Entry state receives
94.46% learned weight; player identity0.67%, first bowler0.31%, form3.61%.
6,241test rows are cold-player cases. Do not claim powerful player-specific
score prediction from this experiment.50+/100+ probabilities are sums of the
same coherent score-bin distribution, not independent incompatible percentages.
Only912test50+ and67test100+ outcomes exist. Binary reports use the two-class
multiclass Brier convention (twice single-event Brier); their top-label reliability
is dominated by negatives and does not establish calibrated rare-century forecasts.

Match target is one canonical sorted-team joint outcome: teamAwin/teamBwin/tie.
Winner is used if explicit; otherwise a tied regulation result is retained, not
the super-over eliminator winner. TeamB recent form is reversed into the SAME
output space. No separately fitted contradictory win percentages. Training-only
tables plus prior completed-date team form; no actual final scores/rankings/toss
or unsupported crowd/home coefficients.

| Joint match-result metric | Global | Rivalry reference | Candidate |
|---|---:|---:|---:|
| Log loss | 0.73654 | 0.72697 | 0.70914 |
| Multiclass Brier | 0.50814 | 0.49758 | 0.48147 |
| Top-label10-bin calibration error | 0.07366 | 0.09879 | 0.11258 |

Log-loss improvement versus rivalry has95%whole-match interval[-0.02573,-0.01116],
but held-out calibration WORSENS. Calibration-only fitting did not prevent date
shift. This candidate needs further independently preregistered calibration work;
no promotion or current win-probability API is added. Both preselected candidates
were retained regardless of these results; no test-driven tuning was performed.

Reproduce:

```powershell
python -m criclytics_app.ml.innings_outcomes --raw-dir data/raw/t20s_male_json --output build/fresh-private-outcome-run --cutoff 2026-10-29
```

The output directory must be fresh/private. Browser Model evidence panels show the actual aggregate report and
limitations; static output contains evaluation only, never model weights/raw rows.
The internal predict helper is not a public trusted-artifact/as-of service. Do not
wire a historical form snapshot into an earlier/current forecast without a separate
hash-verified loader, age display, applicability and prospective release gates.

103tests102pass/one optional skip, including future-outcome changes that cannot
alter training/calibration parameters, sequence-before-target capture, coherent
normalization and nested thresholds. Actual375/1440research-table interaction
passed. No source API calls, deployment, remote Git operation or live claim.
