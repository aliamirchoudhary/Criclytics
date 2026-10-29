# Pre-plan audit remediation — T041A

Implemented locally on `fix/pre-plan-audit-findings`, based on `d7a1599`.
The dated [audit](PRE_PLAN_AUDIT.md) remains the record of what was found.
This document records the resulting behavior and migration; it does not approve
production release, close credential rotations or start T042.

| Finding | Implemented correction | Verification / limit |
|---|---|---|
| A01 | Schedule/photo legacy CLIs are inert and exit before I/O. Photo helpers in the old live module also reject use. | Mocked entry-point and helper tests prove no network/pickle loading. Existing live/rankings/matches source gates remain. |
| A02 | Removed keyed URL/exception logging and credential-prefix printing from remaining provider CLI helpers. Removed the process-global socket timeout/reachability probe. | Synthetic credential-bearing exception tests for live/matches helpers pass without printing values or URLs. Retired schedule path has no logging/network code. |
| A03 | No root JSON/match fallback. Default history is unselected; verified DATASET_STORE, explicit private PROCESSED_DIR or explicit legacy-archive opt-in selects data. | Missing-file/match cross-generation tests, default/opt-in tests, corrected artifact and existing API tests. Original files are not changed. |
| A04 | Docker context is default-deny; only runtime package, launchers, locked dependencies, hosting README and data/static are allowed. Nested private-file exclusions match staging. | Temporary stage contains no private models/database/env files. Actual Docker image execution remains pending: local Docker daemon is not running. |
| A05 | Archived 18 disconnected page scripts, old styles.css, and unused sanitizer/provenance outside public/runtime output. Active DOM/API/media/experience/application/coaching scripts remain. | All19 pages plus navigation/search checked at375/1440px; builds have148 public files versus170 before cleanup. Current page URLs remain; retired asset URLs now404. |
| A06 | Removed unused imports/locals, replaced a misleading delayed-closure name lifetime with explicit calibration inputs. Duplicate photo maps are archived with the retired code. | Isolated Ruff F/E9 has zero diagnostics. Scoring/model fixtures pass; no model was retrained or promoted. |
| A07 | Archived obsolete heuristic/training implementations as non-executable historical text. Compatibility entry points cannot deserialize pickle. | Mocked pickle-load regression tests; original private model artifacts remain untouched. |
| A08 | Readiness independently reports historical, scenario, optional-feed and issued-forecast capability; match eligibility stays unknown until a match-specific read. Removed invented worker/thread observations. | Tests exercise loaded feature objects with missing history;503 remains historical-data readiness, while liveness remains200. No private paths or forecast issuance in readiness. |
| A09 | API domains own their handlers under the same blueprint/endpoint names; summary projections moved to pipeline/summaries.py with compatibility exports. Removed the unused heuristic enrichment/50% fallback and narrowed selected legacy catches. Formatted the extracted API/pipeline seams. | Existing API path/method, golden scoring, dataset/identity, forecasting and pipeline tests. Broad cache-recovery boundaries that deliberately preserve last-good data are retained rather than blindly removed. |
| A10 | Retired unlicensed photo-fetch/metadata-rewrite paths and removed their active documentation claims. Their text is clearly historical. | Current photo workflow remains the identity-bound rights/provenance manifest in PLAYER_MEDIA_SOURCE_PLAN.md and MEDIA_ASSETS.md; no new image or source collection. |
| A11 | CI adds JS syntax and fictional-fixture browser interaction/security checks. Container is digest-pinned, has no build-essential and uses uid1000. Release inventory guard fails closed on unexpected remote files without deleting them. | Local syntax/browser/security/build checks and inventory-set tests. Registry and Hub independently returned the same base index digest. No hosted workflow, remote inventory or container execution claimed. Workflows require public standard runners, with timeouts, to avoid private billed allowance. |
| A12 | README, architecture, dataset configuration, Git workflow and ticket introduction now identify current behavior and the cleanup checkpoint. Initial architecture prose is archived. | Current entry point is README -> this migration/audit -> active ticket. Historical ticket evidence/status tables remain historical rather than rewritten as reviewed/integrated. |

## Operator migration

1. Keep existing data, raw archives, identity stores, model hashes and `.env`.
2. For a new/production process, configure `DATASET_STORE` according to DATASETS.md
   and restart to select a verified immutable generation. An explicit private
   `PROCESSED_DIR` remains supported for local candidates and fixtures. An empty
   setting no longer selects the original archive automatically.
3. Use `LEGACY_DATA_ENABLED=1` only for deliberate local inspection of original
   processed artifacts; their known statistical/identity defects remain. This
   mode never enables root-file fallback. Do not label it a corrected release.
4. Active pages need no URL changes. Old disconnected JS/style URLs now404;
   do not embed those scripts in a downstream site. Public API URLs/methods and
   `api.*` endpoint identities are unchanged. Internal test/tool monkeypatches
   now target their owning API domain.
5. Historical readiness remains the `/api/ready` status criterion. Read the new
   separate feature fields; `model.available` means an experimental artifact is
   loaded, not validated live forecasts. Worker/thread counts belong to the
   deployment configuration and are no longer claimed as observations.
6. Stage a backend before an authorized release. `python -m
   scripts.verify_backend_inventory --repo <space-id>` is read-only and blocks
   upload if old remote files are outside the stage. Review/retain/migrate those
   files deliberately; the script neither deletes nor displays suspicious names.
   Withholding deletion preserves resources, but a blocked inventory is not a
   completed production cleanup.

The current pinned base is
`python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159`,
verified on2026-10-29 against the Docker Registry and
[Docker Official Python tag metadata](https://hub.docker.com/v2/repositories/library/python/tags/3.12-slim).
Digest pins need periodic security review; they do not provide automatic updates.

## Acceptance and remaining work

Evidence is in [audit/audit-remediation-t041a-2026-10-29.json](audit/audit-remediation-t041a-2026-10-29.json).
Routine tests, compilation, isolated core lint, current JS syntax, clean staging,
fictional mobile/desktop interactions and DOM/CSP checks were run locally.
The optional legacy snapshot fingerprints now opt into the original directory;
they are not the corrected statistical contract and remain optional.

Docker daemon execution, hosted CI/release, remote inventory review and T001
credential rotations remain unverified/pending. No new source approval, reliable
live feed, durable automatic publication, paid service, real-user pilot or model
promotion is implied. No remote Git action or deployment was performed. The
owner's existing UI preview and selected/private datasets were not restarted or
rewritten. T042 and the larger platform plan remain paused for UI review.
