# Resumed-session handoff ? 2026-10-28

Local code/tooling work is complete through T030; T031 independent readiness is
prepared, while actual pilot/public release remain blocked. No ticket is marked
remotely integrated/Done. Current branch: `work/t031-release-readiness`, chained
through every preceding local ticket branch. All work stayed $0 with no card.

| Ticket | Local commit | Result |
|---|---|---|
| T017A | ba6525a | Source-ID player aggregates, aliases/collision recovery;6,651matches,5,125rostered/5,050scored IDs;all context/record totals reconcile |
| T027 | 7e3122a | Default-off local trusted shadow API and immutable issued history |
| T028 | 381c27d | Manual/replay workspace, real issued anchors, correction/stale/expiry/retry flows |
| T029 | 98408cf | Identity scouting and page-memory private plan export/import;real feedback pending |
| T030 | 361fe3c; protocol0e3b5b0 | Frozen baselines/first-issue timing+feature audit;actual prospective cohort0, metricsnull/NO-GO |
| T031 | latest local commit on current branch | Independent artifacts/restore/runbook verified;actual coach pilot/release blocked |

Verification:89unit tests88pass/one optional legacy snapshot skip on BOTH Python3.11
and3.12; compilation and active JS syntax pass; both environments pass uv package
compatibility;31pinned runtime packages have0known advisories in the2026-10-28 audit.
The19page/five-width browser matrix has95passing cases plus4interactions. Focused
workspace and real-data scouting/private-plan simulations also pass. See individual
reports under audit/; these are not human coach trials or hosted guarantees.

T017A candidate is build/player-ids-v1-final, opt-in only. Existing13processed
artifact hashes remain unchanged. Source-ID build runs/year/opponent/venue/record
reconciliation passes. Experimental model remains unpromoted. T030's actual report
is separate from its explicitly authored virtual-clock fixture. Optional context
families remain excluded; no pressure/mental-state/weather effect is invented.

The isolated restore drill preserved source/collector coordinator/issued ledger,
kill state, original hashes and immutable issued payload, and retained both dataset
versions through A->B->A selection. Clean public/backend artifacts and offline
private-path/CSP/readiness smoke pass. Hosted restore remains unverified.

Deployment URLs: none created or changed. No deployment occurred. No provider
account/credential or permanent global configuration changed. No messages were
sent to outside parties. Main remains ef7c279; dev remains e4f7ab4. No push, merge,
rebase, reset, tag, PR modification or remote repository mutation occurred.

Unmet gates: T001 owner credential rotations/real-host containment, T013 remote
CI/branch/host/free-resource/rollback verification, T029 real coach feedback,
T030 future permitted30-match/5,000-attempt reviewed timing cohort, and T031 actual
pilot/release review. These cannot be replaced by simulated data or invented
feedback. Authentication instructions are in AUTHENTICATION.md; the owner deferred
those tasks, so no repeat request was made. OPERATIONS_RUNBOOK.md gives the concrete
pilot, incident, restore and release checklist and scope exclusions.

Git actions awaiting explicit approval: integration of the final local branch
into dev, any dev/main release merge, pushes/PR changes and remote backend uploads
that create commits. Nothing was committed on main/dev/pre-existing branches.
Review and approval are still required; this handoff does not grant them.

## Changed files in this resumed session

Base: T02624b42a8, before T017A implementation. Original raw/processed/models are
excluded from this change list; new candidates and environments stay ignored.

- `README.md`
- `criclytics_app/__init__.py`
- `criclytics_app/api/forecasts.py`
- `criclytics_app/api/routes.py`
- `criclytics_app/api/scouting.py`
- `criclytics_app/ml/shadow_baselines.py`
- `criclytics_app/ml/shadow_evaluation.py`
- `criclytics_app/pipeline/cricsheet.py`
- `criclytics_app/pipeline/player_id_stats.py`
- `criclytics_app/pipeline/scouting.py`
- `criclytics_app/services/forecasts.py`
- `criclytics_app/services/player_id_stats.py`
- `criclytics_app/services/reconciliation.py`
- `criclytics_app/services/scouting.py`
- `criclytics_app/static/css/application.css`
- `criclytics_app/static/js/api-client.js`
- `criclytics_app/static/js/application.js`
- `criclytics_app/static/js/coaching.js`
- `criclytics_app/templates/about.html`
- `criclytics_app/templates/compare.html`
- `criclytics_app/templates/data-sources.html`
- `criclytics_app/templates/disclaimer.html`
- `criclytics_app/templates/index.html`
- `criclytics_app/templates/match-detail.html`
- `criclytics_app/templates/match-upcoming.html`
- `criclytics_app/templates/matches.html`
- `criclytics_app/templates/player-profile.html`
- `criclytics_app/templates/players.html`
- `criclytics_app/templates/rankings.html`
- `criclytics_app/templates/records.html`
- `criclytics_app/templates/scouting.html`
- `criclytics_app/templates/search.html`
- `criclytics_app/templates/team-profile.html`
- `criclytics_app/templates/teams.html`
- `criclytics_app/templates/venue-profile.html`
- `criclytics_app/templates/venues.html`
- `criclytics_app/templates/workspace.html`
- `criclytics_app/web/routes.py`
- `docs/ARCHITECTURE.md`
- `docs/COACH_SCOUTING.md`
- `docs/FORECAST_API.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/PLAYER_ID_AGGREGATES.md`
- `docs/SESSION_HANDOFF.md`
- `docs/SESSION_PROGRESS.md`
- `docs/SHADOW_EVALUATION.md`
- `docs/SHADOW_PROTOCOL.md`
- `docs/WORKSPACE_UI.md`
- `docs/audit/application-ui-t028-2026-10-28.json`
- `docs/audit/application-ui-t029-2026-10-28.json`
- `docs/audit/coach-workflow-2026-10-28.json`
- `docs/audit/forecast-service-2026-10-28.json`
- `docs/audit/forecast-service-t030-2026-10-28.json`
- `docs/audit/player-id-aggregates-2026-10-28.json`
- `docs/audit/prospective-shadow-2026-10-28.json`
- `docs/audit/release-preflight-2026-10-28.json`
- `docs/audit/scouting-sample-2026-10-28.json`
- `docs/audit/shadow-artifacts-2026-10-28.json`
- `docs/audit/shadow-tooling-fixture-2026-10-28.json`
- `docs/audit/workspace-ui-2026-10-28.json`
- `docs/coach-pilot-feedback.example.json`
- `docs/shadow-cohort.example.json`
- `tests/test_forecasts.py`
- `tests/test_frontend_build.py`
- `tests/test_player_id_stats.py`
- `tests/test_scouting.py`
- `tests/test_shadow_evaluation.py`
- `tickets.md`
- `tickets/t017a-migrate-player-aggregates-to-source-identities.md`
- `tickets/t027-serve-versioned-next-delivery-probabilities-and-forecasts.md`
- `tickets/t028-build-truthful-live-prediction-workspace.md`
- `tickets/t029-build-coach-scouting-scenarios-and-private-workflows.md`
- `tickets/t030-run-prospective-shadow-evaluation-and-context-ablations.md`
- `tickets/t031-release-measured-coach-pilot-and-operations-runbook.md`
- `tools/check_application_ui.py`
- `tools/check_coach_workflow.py`
- `tools/check_forecast_service.py`
- `tools/check_player_id_stats.py`
- `tools/check_shadow_evaluation.py`
- `tools/check_workspace_ui.py`
- `tools/release_preflight.py`
