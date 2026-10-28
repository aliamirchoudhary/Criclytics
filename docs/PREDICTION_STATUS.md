# Prediction availability

No predictive model is released. Every legacy `/api/predict/*` route preserves
its URL/method but returns HTTP 200 with available=false, kind=unavailable,
source=legacy_heuristics_withdrawn, probability/confidence/cutoff/sample_count=null,
validated=false, model_id=null and an explicit unavailable_reason. Invalid inputs
still use the T004 error contract. Leaderboards evaluate zero players and return
an empty list; they cannot silently represent a first-100-name sample as coverage.

The old formulas are archived in ml/legacy_probability.py with initialization
blocked. They were heuristics, not trained next-delivery models; they accessed
incompatible H2H/team/venue shapes, reversed normal tails, clipped arbitrary
scores and invented confidence/default 50%. Fixing one tail would not validate
the estimator. T008 therefore withdraws all estimates rather than serving a
partially repaired formula. P100<=P50/finite/unit invariants apply when estimates
are reintroduced in T020/T027; there are no supported numeric estimates now.
Tests specifically cover SC Cook/Test, unknown entities, all five metrics,
team/venue schema-independent containment and every prediction route, even with
an injected legacy engine. This does not validate historical summary statistics.

The compatibility ProbabilityEngine is lightweight and returns availability
metadata only; factory initialization defaults off. It never reads saved pickle
artifacts. Browser widgets show unavailable, without arbitrary confidence or
percentages. Comparison heuristic percentages and H2H-derived win forecasts were
removed. Twelve Chrome cases at 375/1440 cover six surfaces; other APIs were made
unavailable and external assets blocked, so this is not full live UI acceptance.

The opt-in legacy prediction response fingerprints are deliberately retired;
focused availability contracts replace them. Historical statistical fingerprints
remain until the explicit T009 schema/statistical migration. Rollback must keep
predictions disabled; do not republish archived formulas. Releasing a model needs
chronological match-grouped held-out evaluation, calibration, model/data identity,
cutoff, target semantics and an as-of state/feature contract (T018-T020/T027).

T020 adds a local experimental CPU next-attempt model with chronological held-out
metrics and separate temperature calibration. It is not promoted; legacy API
availability stays false. MODEL_CARD.md and BASELINE_PROTOCOL.md record scope,
failed training convergence/amendment, trusted JSON identity and limits. Unknown
historical source availability and the small/stale sample preclude live claims.
