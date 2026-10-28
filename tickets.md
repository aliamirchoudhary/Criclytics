# Criclytics implementation tickets

Read [the audit](docs/AUDIT.md), [architecture](docs/ARCHITECTURE.md),
[roadmap](docs/ROADMAP.md), and [branch workflow](docs/GIT_WORKFLOW.md) first.
Each ticket has its own specification and branch cut from dev. Work one ready
ticket at a time; this backlog is not an instruction to implement everything now.

T000 is implemented in the current worktree, awaiting review/integration. T001
requires operator credential/deployment actions. T002 is the next local ticket
after this structure branch is reviewed. T003/T004/T008 are urgent containment.
Follow dependencies; pending operator actions do not prevent independent local
repairs. T024 is optional research and is not a launch prerequisite.

P0 = critical containment/correctness; P1 = required foundation; P2 = later
product/context; P3 = optional research. Planned does not imply dependencies
are complete. Every ticket contains scope, acceptance, validation and handoff.

| Ticket | Outcome | Priority | Dependencies | Status |
|---|---|---|---|---|
| [T000](tickets/t000-audit-and-flask-package-migration.md) | Audit and Flask package migration | P0 | None | Implemented, awaiting review |
| [T001](tickets/t001-rotate-exposed-credentials-and-verify-public-file-containment.md) | Rotate exposed credentials and verify public-file containment | P0 | T000 | Waiting for operator |
| [T002](tickets/t002-upgrade-vulnerable-dependencies-and-verify-compatibility.md) | Upgrade vulnerable dependencies and verify compatibility | P0 | T000 | Implemented; local review pending |
| [T003](tickets/t003-remove-dom-injection-hazards-and-tighten-browser-policy.md) | Remove DOM injection hazards and tighten browser policy | P0 | T000 | Implemented; local review pending |
| [T004](tickets/t004-validate-api-inputs-and-standardize-errors.md) | Validate API inputs and standardize errors | P1 | T000 | Implemented; local review pending |
| [T005](tickets/t005-paginate-compact-match-summaries-and-update-callers.md) | Paginate compact match summaries and update callers | P1 | T004 | Implemented; local review pending |
| [T006](tickets/t006-extract-safe-data-repositories-and-bounded-cache-refresh.md) | Extract safe data repositories and bounded cache refresh | P1 | T004,T005 | Implemented; local review pending |
| [T007](tickets/t007-correct-ranking-and-fixture-freshness-provenance.md) | Correct ranking and fixture freshness/provenance | P1 | T004,T006 | Implemented; local review pending |
| [T008](tickets/t008-contain-misleading-probabilities-and-validate-legacy-contracts.md) | Contain misleading probabilities and validate legacy contracts | P0 | T000,T004 | Implemented; local review pending |
| [T009](tickets/t009-correct-delivery-and-innings-cricket-aggregation.md) | Correct delivery and innings cricket aggregation | P0 | T008 | Implemented; local review pending |
| [T010](tickets/t010-add-golden-cricket-fixtures-and-data-schema-contracts.md) | Add golden cricket fixtures and data-schema contracts | P1 | T004,T009 | Implemented; local review pending |
| [T011](tickets/t011-repair-ui-behavior-empty-states-and-accessibility.md) | Repair UI behavior empty states and accessibility | P1 | T004,T007,T008 | Implemented; local review pending |
| [T012](tickets/t012-consolidate-frontend-initialization-and-api-configuration.md) | Consolidate frontend initialization and API configuration | P2 | T003,T005,T011 | Implemented; local review pending |
| [T013](tickets/t013-verify-ci-deployment-artifacts-branch-controls-and-rollback.md) | Verify CI deployment artifacts branch controls and rollback | P1 | T001,T002,T003,T010 | Blocked; T001 operator prerequisite |
| [T013a](tickets/t013a-cloudflare-assets-build.md) | Generate frontend assets before Cloudflare upload | P1 | T000 | Implemented locally; operator setup pending |
| [T014](tickets/t014-add-safe-diagnostics-readiness-and-resource-budgets.md) | Add safe diagnostics readiness and resource budgets | P1 | T004,T006 | Implemented; local review pending |
| [T015](tickets/t015-version-datasets-source-rights-and-reproducible-builds.md) | Version datasets source rights and reproducible builds | P1 | T009,T010 | Implemented; local review pending |
| [T016](tickets/t016-prove-permitted-zero-budget-live-data-feasibility.md) | Prove permitted zero-budget live data feasibility | P1 | T015 | Implemented; replay/manual decision |
| [T017](tickets/t017-introduce-stable-cricket-identities-and-provider-mappings.md) | Introduce stable cricket identities and provider mappings | P1 | T015 | Implemented; local review pending |
| [T018](tickets/t018-build-canonical-delivery-events-and-deterministic-replay.md) | Build canonical delivery events and deterministic replay | P1 | T010,T015,T017 | Implemented; local review pending |
| [T019](tickets/t019-create-before-delivery-features-and-coherent-outcome-labels.md) | Create before-delivery features and coherent outcome labels | P1 | T018 | Implemented; local review pending |
| [T020](tickets/t020-train-and-evaluate-a-calibrated-cpu-baseline.md) | Train and evaluate a calibrated CPU baseline | P1 | T019,T014 | Implemented; experimental not promoted |
| [T021](tickets/t021-evaluate-weather-context-without-hindsight-leakage.md) | Evaluate weather context without hindsight leakage | P2 | T016,T019,T020 | Planned |
| [T022](tickets/t022-add-lineup-matchup-and-pitch-context-feature-families.md) | Add lineup matchup and pitch-context feature families | P2 | T017,T019,T020 | Planned |
| [T023](tickets/t023-support-attributed-fielding-and-incident-annotations.md) | Support attributed fielding and incident annotations | P2 | T018,T019 | Planned |
| [T024](tickets/t024-research-media-and-crowd-context-only-if-measurable.md) | Research media and crowd context only if measurable | P3 | T015,T020,T023 | Planned |
| [T025](tickets/t025-implement-one-permitted-budgeted-live-collector.md) | Implement one permitted budgeted live collector | P1 | T006,T014,T016,T017,T018 | Planned |
| [T026](tickets/t026-reconcile-live-state-corrections-and-replay-parity.md) | Reconcile live state corrections and replay parity | P1 | T018,T019,T025 | Planned |
| [T027](tickets/t027-serve-versioned-next-delivery-probabilities-and-forecasts.md) | Serve versioned next-delivery probabilities and forecasts | P1 | T020,T026,T014 | Planned |
| [T028](tickets/t028-build-truthful-live-prediction-workspace.md) | Build truthful live prediction workspace | P1 | T011,T012,T027 | Planned |
| [T029](tickets/t029-build-coach-scouting-scenarios-and-private-workflows.md) | Build coach scouting scenarios and private workflows | P2 | T010,T012,T017,T020,T023 | Planned |
| [T030](tickets/t030-run-prospective-shadow-evaluation-and-context-ablations.md) | Run prospective shadow evaluation and context ablations | P1 | T020,T027,T028 | Planned |
| [T031](tickets/t031-release-measured-coach-pilot-and-operations-runbook.md) | Release measured coach pilot and operations runbook | P1 | T001,T002,T003,T013,T014,T015,T028,T029,T030 | Planned |

## Agent handoff

Use: "Implement Txxx from its ticket on a new branch from dev. Follow AGENTS.md,
keep within scope/$0 constraints, run acceptance checks, update evidence and
prepare a focused review. Do not deploy/push or start another ticket unless
that action is authorized."

Statuses: Planned -> In progress -> Implemented, awaiting review -> Done.
Use Waiting for operator or Blocked with a concrete dependency when applicable.
Split oversized discoveries into explicit child tickets and update dependencies
before broad implementation. The current restructuring must be committed and
reviewed before switching to a new ticket branch; preserve uncommitted work.
