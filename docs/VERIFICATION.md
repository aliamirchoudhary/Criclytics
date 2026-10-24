# Migration verification — 2026-10-25

Work is on `chore/audit-and-flask-structure`, based on new local `dev` from local
main `ef7c279`. Main's original one-commit lead over origin is preserved. No
commit, push, merge, remote protection change, credential rotation or deployment
was performed. Changes remain available for review in the current worktree.

## Executed checks

- Python compilation: application, pipeline/integrations/ML modules, scripts,
  diagnostic tools, tests and both entry points.
- `node --check`: all 17 JavaScript files passed syntax checking.
- Offline unittest suite: public/private file boundaries, all 17 pages and their
  local assets, preserved API route methods, safe bootstrap serialization, CORS,
  alternate working directory, no upstream fetch in offline mode, legacy public
  asset redirects and clean public frontend build. A separate full-data test
  checks 12 pre-migration API response SHA256 fingerprints from the original local
  data. These deliberately preserve legacy statistical behavior, not validate it.
- Full-data command: set `CRICLYTICS_FULL_DATA_TESTS=1`, then
  `python -m unittest discover -s tests -v`. Normal CI does not require the ignored
  data snapshot and explicitly skips this optional test.
- Final full-data run: all 12 tests passed in approximately 15 seconds, including
  backend allowlist staging and refusing a frontend output directory containing
  an unexpected file. Python compilation and `git diff --check` also passed.
- Static/frontend and allowlisted backend artifacts built successfully; initial
  file inventories were 39 and 67 files respectively. Inspection found no `.env`,
  `.git`, raw data, model pickle or bytecode files. Builders require clean output
  directories to prevent retaining old unexpected files.
- Chromium: 17 pages at 375px and 1440px, 34 cases total. Real local historical
  corpus, cached rankings and blocked third-party image/font/icon requests. No
  document-level overflow or local HTTP failure in those cases. Team-profile
  image fallback emitted a null-parent error at both widths; it is recorded in
  T011 and intentionally not mixed into the structure migration.
- Dependency audit: `pip-audit 2.10.1`, pinned requirements, public PyPI advisory
  lookup. Reported 25 entries, 16 unique package/advisory pairs across seven
  packages. T002 remains open; the main release gate intentionally blocks on it.
- Ticket graph: 32 files, each with scope, dependency, acceptance and validation;
  references resolve and dependency graph has no cycles.
- Safe current Python credential-pattern scan reports locations only, never
  values. The known debug-script literal was removed; this does not certify full
  history clean or revoke any old credential.

## Evidence

- [Original measurements and counts](audit/baseline.json)
- [Dependency package/advisory summary](audit/dependency-findings.json)
- [Full browser case output](audit/browser.json)
- [Mobile home screenshot](audit/screenshots/index.html-375.png)
- [Desktop home screenshot](audit/screenshots/index.html-1440.png)
- [Team fallback reproduction](audit/screenshots/team-profile.html-375.png)
- `tests/fixtures/legacy_routes.json`, `tests/fixtures/legacy_responses.json`

Screenshots intentionally omit blocked external fonts/icons/photos; they do not
constitute production visual approval. The test database/source snapshot has not
been regenerated. Original Office reports, presentation and prior untracked notes
were moved into `docs/history/` without content changes.

## Not verified / not fixed

No production secret retrieval or provider feed calls were performed. Remote
host/account settings, Windows versus Linux container execution, full interaction
and accessibility acceptance, cross-browser rendering, multi-worker concurrency,
long-duration load, complete Git-history secret scans and live-source rights are
pending their respective tickets. Existing statistical/ETL/model defects remain
explicitly listed in the audit. Current passing migration tests do not establish
coaching or predictive validity.

Docker CLI is installed, but the local Linux engine pipe was unavailable. The
read-only daemon check also failed outside the sandbox, so no container build or
runtime smoke is claimed. T013 must perform that check with a running engine.

Audit utilities were installed temporarily outside the project, not added to
runtime requirements. Local source credentials were never used by the audit's
provider HTTP checks; browser upstream assets were blocked. Operator rotation
and production containment in T001 remain urgent release work.
