# Pre-plan engineering audit — 2026-10-29

Baseline: `6f7356a` (T041), inspected on `audit/pre-plan-health-check`.
This is an audit, not implementation of the next roadmap. The application,
selected datasets, models, credentials, hosted resources and owner's UI preview
were not changed. The previous AUDIT.md remains the dated original baseline.

The foundation passes its offline checks, but it is **not yet clean enough to
declare everything fine**. In particular, legacy command-line collectors do not
consistently obey the newer source boundary, and data selection still permits
legacy fallbacks. Priorities below describe the affected execution path; a CLI
defect is not evidence of a remotely exploitable web endpoint.

## Verified findings

| ID / priority | Finding and evidence | Required correction before expansion |
|---|---|---|
| A01 / P1 | `integrations/schedule.py:196` calls its HTTP helper without `require_source`. With `source_allowed('cricapi') == False`, a mocked successful run still attempts two calls. `integrations/photos.py:27,150` likewise has a directly executable network path without the reviewed source gate. Normal live/matches/rankings adapters do have gates. | Retire these old CLIs or put every network entry point behind the same reviewed source policy and bounded collector contract. Test the CLI paths, not only the Flask helper. |
| A02 / P1 | `integrations/schedule.py:44` prints an exception containing a provider URL. A synthetic `URLError` carrying a synthetic keyed URL reproduced key disclosure in captured stdout. No real key was printed and no network request was made. | Log fixed error categories, never exception text or keyed URLs. Add a synthetic-secret regression check. This is an operator/log exposure, not a demonstrated public endpoint leak. |
| A03 / P1 | `services/legacy.py:52–70` falls back to checkout-root JSON when a selected artifact or match is absent. A temporary selected directory plus temporary legacy records file returned the legacy record. The default factory (`__init__.py:19`) also chooses original `data/processed` unless explicitly overridden. | Make verified dataset selection explicit and strict; missing selected data must not silently mix generations. Preserve original artifacts as archives. Document deliberate compatibility mode separately. |
| A04 / P1 | Docker's direct-checkout path uses `COPY . .`; `.dockerignore` omits `models/` and `data/processed/`. Six existing pickle artifacts are therefore not excluded by that boundary. | Require the allowlisted stage as the build context or harden the direct context. Current staged-backend verification found no private artifacts; this finding concerns direct checkout builds, not a claim that those files were uploaded. |
| A05 / P2 | Eighteen top-level JS files are not loaded by any current template; legacy JS references only connect parts of that disconnected graph. `styles.css` is also not linked by current templates. Both build utilities still copy all static assets. | Preserve history, then remove retired assets from public output after checking external compatibility requirements. Do not maintain two frontend implementations indefinitely. Full inventory is in the evidence JSON. |
| A06 / P2 | Isolated Ruff F/E9 scan returns 57 diagnostics: 40 unused imports, 10 unused locals, two redundant f-string prefixes, four duplicate dictionary keys, one apparent undefined name. Duplicate keys are in `integrations/photos.py:55,83,99,124`; later values silently overwrite earlier values. | Triage imports/re-exports and remove actual dead bindings; deduplicate mappings deliberately. The apparent undefined `mixture` in contextual.py is **not confirmed broken**: SciPy executes its closure synchronously before the subsequent `del`. Do not blindly autofix. |
| A07 / P2 | `ml/legacy_probability.py:34` intentionally raises before its old implementation: this is known unreachable archived code, not a new regression. `ml/training.py:120,122` still deserializes pickle in the legacy training/loading path. | Move explanatory archives out of the runtime package and retire obsolete executable model loaders when references are removed. Never accept untrusted pickle. Current serving uses the unavailable facade / explicit hashed JSON candidates; no web pickle RCE was demonstrated. |
| A08 / P2 | `services/diagnostics.py:readiness` always reports `model.available: false`, even though scenario/forecast initialization now has independent configuration and availability. Worker/thread figures are constants. | Report separate actual historical-data, scenario-model, live-source and issued-forecast readiness with bounded safe metadata. Keep liveness distinct from feature readiness and document fixed deployment assumptions. |
| A09 / P2 | `api/routes.py` remains 1,030 lines and `pipeline/cricsheet.py` 932 lines. Legacy service fallbacks, broad exception handling and substantial compressed one-line code make contracts and failure paths hard to review. | Split by domain after behavioral contracts are captured; distinguish unavailable, corrupt and empty data. Do not mechanically rewrite the pipeline while changing statistical semantics. |
| A10 / P2 | The legacy photos module describes Wikipedia images as public domain and discusses unofficial/VPN sources (`photos.py:1–8`). Its old main rewrites metadata directly without the newer per-image license/provenance manifest. Wikipedia-hosted content does not itself establish that license claim. | Retire that route in favor of the reviewed media-manifest workflow. Require per-image rights, attribution, identity verification and atomic publication; do not execute this CLI to expand photo coverage. |
| A11 / P2 | CI runs tests, compilation and staging but no JS syntax or browser checks. Release uploads add staged files but the workflow does not establish removal of previously uploaded remote files. Docker retains build-essential and runs as root; the base tag is mutable. | Add inexpensive static frontend checks and targeted browser regression checks; verify remote inventory during an explicitly authorized release. Harden the runtime image. Absence of deletion flags alone does not prove a remote secret exists. |
| A12 / P2 | Root README/ticket-index introduction still directs work toward the initial roadmap/T002; ARCHITECTURE's tree says 17 pages and calls the served engine a heuristic. Actual templates number 19 and the facade withdraws that engine. GIT_WORKFLOW also retains original setup text above its newer session override. | Provide one current entry point and label historical status prose clearly. Keep detailed historical reports, but avoid making operators infer which of several handoffs describes current serving behavior. |

Paths in this table are relative to `criclytics_app/` unless explicitly named.
P1 requires correction before relying on the affected path; P2 is engineering
debt to schedule before further substantial expansion. No new P0 public exploit
was reproduced in this audit. Previously exposed credentials remain an unresolved
operator risk until rotation; this audit does not close T001.

## Checks and interpretation

- Fresh suite: **106 tests run, 105 passed, one optional skip**. Passing checks
  do not establish that every CLI entry point or deployment is covered.
- Fresh hash-locked dependency audit: **31 packages, zero known advisories**.
  The shell captured pip-audit's success message as a PowerShell native stderr
  diagnostic; the generated JSON contains no vulnerabilities. This says nothing
  about future advisories or provider account configuration.
- Python compilation passed. `node --check` passed for all **26 JS files**,
  including vendored code. No source code was changed to achieve these results.
- Fresh temporary builds: **19 frontend pages / 170 frontend files**, **248
  backend files**; the staged backend contained no `.env`, pickle or SQLite
  artifacts. Direct Docker-context construction is a separate issue (A04).
- Flask private-path probes returned **404** for `.env`, `.git/HEAD`, models,
  processed data and audit docs. This verifies local route containment only.
- Bandit emitted 19 warnings. Its eight SQL-construction warnings were reviewed:
  the inspected fragments use fixed table/condition fragments or allowlisted
  identifiers and bind external values as SQL parameters. They are not eight
  verified SQL injection vulnerabilities. Two URL-open warnings concern old
  operator helpers, not user-supplied public URL fetch endpoints. Two pickle
  warnings are retained as A07; low-severity swallowed-exception warnings support
  A09. No automatic security fixes were applied.
- Static unused-code analysis is advisory: Flask registrations, CLI modules,
  archived compatibility seams and synchronous lambdas need human interpretation.
  Ruff was rerun with `--isolated --select F,E9` to avoid inheriting workstation
  lint preferences. Style warnings from the initial broad scan are not counted
  as defects.

Browser smoke: **38 cases (19 pages at 375px and 1440px), zero uncaught page
errors, HTTP failures or document-width overflows**. Results are recorded in
the adjacent evidence JSON.
The browser audit uses a separate local server, desktop/mobile widths and blocked
third-party traffic. Its fixture rankings and default historical data do not
validate current ranking freshness, contextual model configuration, live delivery
ingestion or the owner's actual configured preview. This is separate from the
owner's UI/UX review; it is not visual acceptance or an end-to-end product sign-off.

## Existing product and operational gaps, not new regressions

T041 creates a private corrected candidate; it does not durably publish it or
select it for the website. A local successful refresh is not evidence that a
remote schedule is active. Live next-delivery ingestion remains blocked by source
rights/limits evidence. Weather, crowd and incident records being representable
does not mean those features are populated or their predictive effect validated.
Models remain experimental and are not automatically retrained/promoted by the
refresh job. Per-process caches and a local load exercise do not prove hosted
multi-instance capacity for thousands of users. These limitations must remain
visible rather than being filled with invented values.

No production deployment, provider calls, credential rotation, remote account
audit, Docker execution, full Git-history secret scan, multi-instance soak test,
or prospective model evaluation was performed. No real coach notes were inspected.
The audit cannot certify production security or absence of further bugs.

## Handoff before the next implementation plan

Review A01–A04 first, combine the owner's UI findings with A05/A12, then define a
small cleanup/containment batch with acceptance criteria. Retain the statistical
contracts and original data. Re-run targeted entry-point checks and the existing
suite after fixes. Only then resume dependent platform expansion; this report
does not authorize launching the entire roadmap or publishing anything.

Machine-readable evidence: [pre-plan-audit-2026-10-29.json](audit/pre-plan-audit-2026-10-29.json).
Private raw tool outputs remain under ignored `build/preplan-*`; no credentials
or private data were copied into the public report.

Re-run the suite with `python -m unittest discover -s tests -v`, compilation with
`python -m compileall -q criclytics_app scripts tools app.py wsgi.py`, and the
optional browser smoke with `python -m tools.browser_audit`. Audit-only Ruff,
Vulture and Bandit were installed in an isolated ignored build environment;
they were not added to application dependencies or permanent tool settings.
