# Contextual next-attempt candidate (T034)

Experimental male international six-ball T20I model, not promoted for live use.
The frozen protocol was committed as bb9f496 before fitting. It predicts a joint
delivery attempt (including illegal deliveries), not mutually exclusive labels
such as "six" versus "wicket" that could misrepresent extras or run-outs.

The nine smoothed components cover phase, batter, bowler, exact matchup, venue,
team rivalry and the last five completed matches by role, plus a global prior.
Nonnegative mixture weights and temperature are learned on calibration only.
Same-date history is deferred; frozen training counts never update in the test
partition. Earlier completed held-out dates can update recent form, as declared
in the protocol. Source publication and actual delivery timestamps are unknown.

The local corpus contains 3,249 eligible matches, 2005-02-17 through 2026-04-09;
five multi-date matches were excluded. Whole-date 60/20/20 splits yield 1,632
training, 771 calibration and 846 test matches. The test contains 189,168 attempts,
starting 2024-10-12. Full evidence is in
[the evaluation report](audit/contextual-model-t034-2026-10-29.json).

| Held-out metric | Global | Phase | Contextual |
|---|---:|---:|---:|
| Joint log loss (lower is better) | 1.81203 | 1.78925 | 1.78202 |
| Multiclass Brier | 0.75825 | 0.74846 | 0.74673 |
| Top-label calibration error | 0.02105 | 0.01645 | 0.01377 |

The 200 whole-match bootstrap interval for log-loss difference versus phase is
[-0.00802, -0.00645]. This supports an improvement in this retrospective cohort;
it does not establish prospective accuracy, a six/wicket hit rate, or causality.
Test coverage includes 81,246 cold-batter attempts, 86,326 cold-bowler attempts,
177,834 unseen matchups and 26 unknown joint labels. Sparse players/matchups
mostly back off toward pooled evidence. Phase receives about 62.8% mixture weight;
recent batter and bowler form about 13.2% and 12.0%. The exact pair receives 0.54%.
Do not market a strong personalised advantage that these samples do not support.

Training and evaluation took about 96 seconds on the local CPU. A deterministic
repeat peaked at 596 MB working set; inference loaded at about 76 MB process
working set and took about 0.6 ms median for 1,000 local service calls. Numeric JSON
weights occupy about 10.9 MB and remain ignored under build/contextual-v1-full.
Separate reproducibility/resource measurements are recorded in the resource
report. Training requires substantially more memory than inference. No GPU,
external inference service, token, billing account or card is required.

Run from the repository root:

```powershell
python -m criclytics_app.ml.contextual --raw-dir data/raw/t20s_male_json --output build/contextual-v1-full --cutoff 2026-10-29
```

To serve scenarios configure SCENARIO_MODEL and SCENARIO_EVALUATION with private
artifact paths and SCENARIO_MODEL_SHA256 and SCENARIO_EVALUATION_SHA256 with their
exact trusted hashes. Never place full model files under static/ or dist/.
The default is unavailable; no fabricated fallback. The original issued-forecast
model and ledger remain unchanged. Restart after publishing a new trusted model.

The prediction centre's What-if scenarios tab lets users select both players,
ground, phase and innings, with optional team context. Batter and bowler views
derive from one normalized joint distribution. OTHER produces event bounds, not
confidence intervals. Any-wicket includes non-striker run-outs; it does not mean
the striker is necessarily dismissed. A scenario cannot precede the artifact's
latest form snapshot. Form dates and age are visible; old matches are not current
form simply because the scenario date is today.

Weather, actual pitch measurements, crowd noise, booing, politics, psychological
state and fielding-incident causal effects are unsupported. Scenario phase does
not yet include exact score, chase target, wickets remaining or match pressure.
Only this defined population was evaluated. Whole-innings totals, other formats,
women's cricket and domestic leagues need separate protocols and evidence.

Rollback: unset the four SCENARIO_* settings and restart. The UI shows unavailable
scenarios and retains historical evidence/replay tools. No data migration needed.
