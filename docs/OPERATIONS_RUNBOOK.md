# Release and incident runbook — release blocked

This is independent offline readiness preparation for T031, not a pilot or
deployment completion. Actual coach participants:0. Actual prospective matches:0.
No new deployment URL exists. Original datasets/resources are unchanged, and all
ticket work remains on chained local branches pending operator integration review.

## Gates before public release

| Gate | Current evidence | Required next evidence |
|---|---|---|
| T001 credentials/production containment | Local exposure boundary fixed | Owner rotates/revokes exposed CricAPI/RapidAPI/Redis categories and verifies real deployed bundles/routes; AUTHENTICATION.md |
| T013 host/CI/branch controls | Local builds and allowlists pass | Actual clean CI runs, existing-host settings/free eligibility, supported branch protection or manual release control, hosted rollback |
| Corrected data selection |6,651-match candidate and identity migration pass locally | Review immutable hashes, scope/ODC-BY attribution and explicitly select intended datasets on host; no silent promotion |
| T029 coach usefulness | Browser task simulations only | Real feedback under the pilot protocol below; no invented participants |
| T030 predictive validity | Tooling passes; actual metrics null, NO-GO | Preregistered30-match/5,000-attempt prospective cohort, timing/source coverage and baseline/calibration review |
| Integration/publication | Local commits only | Explicit approval for merges/pushes/PR changes/remote repository mutation; only reviewed main may release |

These gates are not waived by a green local test. There is no claim that all
hidden defects have been found. Do not enable a public prediction endpoint or
call replay a live trial. Source-policy network allowlist remains empty. Preserve
existing services; no paid API, paid model, GPU, metered fallback, card, new compute
resource or billing activation. Recheck actual existing-host terms before release
using LIVE_FEASIBILITY.md; a free compute entitlement is not assumed.

## Verification and artifact boundary

Routine verification is `python -m unittest discover -s tests -v`, compilation,
and `node --check` for active changed JS. Both local Python3.11 and3.12 suites
currently run89tests:88pass/one optional legacy-data skip. `uv pip check --python
<venv-python>` passes both local uv environments (they do not include pip).
The pinned runtime lock audit found zero known advisories on2026-10-28; optional
dev tools/OS/browser and application logic are not certified by that result.

`python -m scripts.build_frontend --output <fresh-external-dir> --api-base
<reviewed-HTTPS-backend-origin>` builds19public pages and assets only. Configure
the matching backend CORS origin; an empty API base intentionally means same
origin, which does not supply a Flask API on Cloudflare static hosting. Use the
exact Workers Builds command from CLOUDFLARE_DEPLOYMENT.md. `python -m
scripts.stage_backend --output <fresh-external-dir>` creates the backend allowlist.
Never upload the checkout. Inspect both artifacts: no env/Git/raw/processed source
trees, build folders, credentials, private plans, CSV/pickle/SQLite/model artifacts.
Reviewed datasets are separate private immutable resources, not public assets.

`python -m tools.release_preflight` uses existing ignored local candidates and
the T031 dependency-audit JSON under build/. It creates fresh temporary artifacts,
blocks network GETs, checks API/CSP/private-path denial and performs an isolated
authored restore drill. It does not deploy, change selected production data or
approve a release. Local report: audit/release-preflight-2026-10-28.json.

Public-ready scope remains descriptive history/scouting with explicit dataset
coverage; private plans are page memory plus local files. Experimental workspace
API is default-off, loopback/same-origin and unpromoted. No hosted private accounts,
live external feed, psychological model or guarantee of future performance.

## Backup and restore

1. Stop the producer and set its local kill flag:
   `python -m criclytics_app.integrations.collector --store <existing-private-store> --kill`.
   Confirm there is no active writer/reserved observation or pending raw commit.
   A kill flag alone does not undo a worker already in flight. Preserve failed/
   pending inputs for investigation and explicit retry; do not delete them.
2. Back up the event SQLite, sibling `.collector.sqlite3` and separate state/issued
   ledger together **after quiescing**. Use SQLite's backup API, not a copy of a
   live main file without its WAL. Keep the producer killed on restore until review.
3. Back up selected dataset versions plus `current.json`/promotion metadata,
   identity registry/player candidate, model/evaluation/baseline artifacts and
   trusted hashes/configuration. Keep at least current and previous reviewed
   versions and an independent private/offline copy within available disk space.
   Secrets belong in the owner's secret manager/local environment, not public
   backup artifacts. Private exported coach plans are backed up by their owner.
4. Restore to a fresh private directory first. Configuration rejects a derived ledger that aliases the raw source or collector-coordinator file. Check SQLite integrity, source/
   dataset/model hashes, exact issued payloads/replacement links, retained kill
   state and source age; run offline API checks before selecting any restored path.
   Do not overwrite source/raw data or reset Git as a rollback mechanism.
5. Dataset rollback uses the existing validated retained version and its trusted
   manifest digest with `python -m criclytics_app.pipeline.artifacts promote
   --candidate <retained-version> --store <private-store> --expected-manifest-sha256
   <reviewed-hash>`, followed by a process restart. Prior versions remain present.
   Restore source and derived ledgers consistently; never rewrite issued forecasts
   to match newly corrected observations.
6. Resume a local producer only after a fresh score/actor/innings confirmation and
   source-policy review using the explicit `--resume` command. Expired confirmations
   require new input. No automatic network provider or paid fallback is selected.

The isolated drill restored all three databases with integrity checks, retained
the kill flag and immutable issued entry, preserved original source/ledger hashes,
and selected versionA -> B -> A while retaining both immutable versions. This is
not a tested hosted volume restoration or recovery-time guarantee. Free ephemeral
disk and sleeping hosts are not durable backups.

## Incident actions

| Trigger | Immediate action | Recovery condition |
|---|---|---|
| Source older than60s, announcement older than15s, gaps/late correction | Show last-good score with age; no current forecast; retain issued history | Fresh consistent pre-attempt confirmation; no unknown timing called live |
| Quota/backoff/kill | Stop collection and abstain; retain existing observations | Operator review within approved source/global caps; no key rotation to evade limits |
| Corrupt dataset/model/SQLite or readiness503 | Keep inference unavailable; preserve files/log categories and trusted hashes | Validated fresh restore/previous immutable version, exact schema checks, restart |
| Suspected secret/private exposure | Block publication; owner follows T001 rotation/host review | Actual containment/credential category evidence with values redacted |
| Wrong probability or late issue found | Disable experimental issuance; retain original forecast/revisions and cohort failure | Independent timing/parity/adjudication review; new protocol/cohort where required |
| Free-host sleep/storage loss | Mark unavailable/stale; restore from operator backup | Reviewed existing free resource actually supports storage/runtime; no keepalive bypass/billing |

Disable `EXPERIMENTAL_FORECASTS` to stop issuance; old public prediction facade
remains unavailable. Use fixed redacted diagnostics: request ID/endpoint/status/
duration, source reason, artifact identity. Never log private notes, raw query
strings, credentials or provider URLs containing keys. Retention ceilings require
explicit operator action; no automatic deletion of source/forecast history.

## Real coach/player pilot protocol — not started

Use at least3actual coaches/players, five tasks each, on local or already-authorized
resources within $0. No outreach/message is authorized by this document. Do not
create accounts, send invitations or claim consent/feedback on someone's behalf.
Store participant aliases/consent/feedback privately; publish only aggregated
counts and limitations after review. Use one operator's local page/file workflow,
not a claimed multi-user private cloud service.

Tasks: choose the correct identity among colliding names; prepare opponent/venue/
bowler evidence with sample scope; explain missing context/OTHER/replay/stale
states; export/restore a private plan; identify source/cutoff and a correction's
original issued entry. Record task completion, duration, errors, misunderstanding
of predictions/privacy, and a short usefulness rating. Predeclare target>=80%
task completion and no severe privacy/false-live misunderstanding before broadening
the pilot. These small usability counts do not validate model performance.

Use `coach-pilot-feedback.example.json` as an empty private-file template. No
server upload or automatic telemetry is supplied. Report actual feedback to the
owner through their chosen private channel only when separately authorized. Keep
failure cases and storage-loss observations. Actual participants/task success/
usefulness currently remain0/null. Predictive promotion still needs T030's distinct
prospective gates and independent real source/timing review.

## Publication and rollback approval

The current session permits local commits on new ticket branches only. Push,
merge/rebase/reset/tag/PR modification and remote repository mutation remain
pending explicit approval. An HF upload can create a remote commit and is included
in that restriction even when invoked through an SDK rather than Git. No such
action occurred. Do not deploy feature branches to evade main-only release rules.
After approval and all gates, use reviewed main artifacts on existing resources
and retain the last safe release/version and dataset manifest. Test actual hosted
private-path containment, health/readiness, configured API/CORS, old unavailable
predictions and honest source modes before announcing release. Roll back to a
retained safe release as a unit; never restore the original root static-serving
configuration or discard raw/issued data. Hosted release/rollback remains pending.
