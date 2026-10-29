# T039: Full innings outcome model

- Status: Research implemented/evaluated; promotion and continuation model pending
- Branch: feat/t039-innings-outcomes
- Base: 5332742
- Protocol: docs/INNINGS_OUTCOME_PROTOCOL.md
- Depends on: T034
- Budget: $0; no card or metered fallback

Register a separate player-score/team-outcome protocol and sequence/survival target. Evaluate on held-out matches with calibration and uncertainty. Do not relabel historical century frequency as a current forecast.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Protocol frozen f70e8e9. Two separate calibrated CPU candidates fitted on3,174
whole-date chronological matches: sequence-derived entry-to-terminal batter runs
and one joint canonical team result. Private numeric artifacts, full provenance,
threshold consistency and whole-match intervals retained. Player candidate has no
clear improvement versus entry baseline; match candidate improves log loss but
worsens held-out calibration. Neither promoted. No counterfactual survival or
in-progress continuation claim. See docs/INNINGS_OUTCOME_MODEL_CARD.md and
docs/audit/innings-outcomes-t039-2026-10-29.json.

Actual aggregate research visible in ML evidence, clearly distinct from live
forecasts/historical frequencies.103tests102pass/one skip; leakage/sequence/
normalization tests, Python compilation/JS syntax and375/1440UI interactions pass.
Real prospective calibration, continuation/sequence simulation and service release
remain future acceptance, not fabricated outputs. No quota/card/deployment/remote.
