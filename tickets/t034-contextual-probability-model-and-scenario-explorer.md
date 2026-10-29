# T034: Contextual probability model and scenario explorer

- Status: Implemented locally; review/promotion pending
- Branch: feat/t034-contextual-model
- Base: e973f8f
- Protocol: docs/CONTEXTUAL_MODEL_PROTOCOL.md (freeze before fitting)
- Depends on: T033,T020,T022
- Budget: $0; no card or metered fallback

Freeze a chronological protocol; train/calibrate/evaluate a CPU contextual candidate; expose bounded player/bowler/venue scenario choices and one joint distribution with batter/bowler event bounds. Retain source samples, form/as-of scope and unsupported feature families. No automatic promotion.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

## Implementation and evidence (2026-10-29)

Protocol frozen in bb9f496 before fitting. CPU model trained on all 3,249 eligible
local T20I matches, including date-group chronology and deferred recent history.
846 held-out matches / 189,168 attempts: contextual log loss1.78202 versus phase
1.78925; whole-match bootstrap delta interval[-0.00802,-0.00645]. See
docs/CONTEXTUAL_MODEL_CARD.md and docs/audit/contextual-model-t034-2026-10-29.json.
Private hash-verified numeric artifacts remain under ignored build/, no pickle.
No automatic promotion, live integration or replacement of earlier issued records.

Bounded read-only scenario API and searchable player/ground choices implemented.
Batter/bowler perspectives share one coherent joint distribution, with OTHER
bounds, sample counts, source/form dates, cold starts and unsupported context.
Context changes invalidate the displayed result; prior-date future-form requests
are rejected. Model unavailable is explicit when configuration is absent.

Verification:94 unit tests,93 pass/one optional legacy skip; training/test leakage
and trusted-artifact guards covered. Actual Chrome375/1440 selection/calculation/
perspective/context-change flows pass: docs/audit/scenario-ui-t034-2026-10-29.json.
Python compilation, changed JS syntax and clean19-page static build pass.
Repeated frozen fitting reproduces identical model bytes and metrics; resource
measurements: docs/audit/contextual-resources-t034-2026-10-29.json.

Limits: retrospective male T20I only; no live/prospective validation. Exact score,
target, wickets remaining, weather, pitch and inferred psychological effects are
not fitted. Recent snapshots can be old; unseen player pairs are common. No push,
merge, deployment, API quota use or billing activation.
