# T033: Audit the original and restore complete cricket workflows

- Status: Implemented; review pending
- Branch: feat/t033-cricket-workflows
- Base: T032 c355d9c (chained per owner instructions)

Owner rejected the T011/T032 loss of useful workflows. Use actual Playwright
interaction with the existing deployed original and local revision. Record a
feature parity inventory and findings, not screenshots alone. Restore browsable
player cards, ready-to-select comparisons, format/category tabs, match-centre
navigation and prominent probability/ML workflows. Audit photo coverage/quality,
cached scoring freshness and obsolete rankings. Restore professional navigation
and compact discovery without removing the project's predictive purpose.

Keep $0/no-card and actual source permissions; do not invent live updates or
validated probabilities. Preserve source identities, original data/resources,
private notes, CSP and safe DOM rendering. Unknown probabilities remain unavailable.
Live-score snapshots and prediction timing are different contracts. A live feed
needs rights/quota evidence; do not silently re-enable a blocked provider.

Acceptance: old and new desktop/mobile interaction evidence; selectable/searchable
comparison candidates with no ID typing; player grid and usable filters; record
and ranking navigation without obsolete rankings posing as current; visible ML /
probability sections linked from entity/match workflows; honest live score centre
and refresh/source age; improved photo delivery where permission exists, with
documented unresolved rights. Run regression/browser checks and update progress.
No push, merge or deployment is authorized by this ticket.


## Evidence and limits

See docs/ORIGINAL_UI_PARITY.md and docs/audit/original-reference-t033-2026-10-29.json
for original Playwright inventory and interactions. Final local matrix:
audit/application-ui-t033-2026-10-29.json (95cases/4interactions). Focused actual
workflows and real external widget: audit/cricket-workflows-t033-2026-10-29.json.
92unit tests:91pass/one optional skip; Python/JS/build checks pass.

Restored actual-data player cards, comparison selection, buttons and six player
views; match scorecard/Probability/ML tabs; discoverable experimental prediction
centre; dated/frozen model report and past joint distributions.37configured
portraits, no hotlinks, provider originals excluded from Git. Free external score
widget loads only on request, cannot access parent/private notes and is not used
as a prediction feed. No timely automated delivery collector or fresh public ICC
redistribution source is established. No model promotion, remote push or deployment.
Owner expanded vision is planned in NEXT_BALL_PLATFORM_PLAN.md and T034?T040.
