# Project audit — 2026-10-25

Baseline: local `main` at `ef7c279`, before restructuring. Work branch:
`chore/audit-and-flask-structure`, based on local `dev`, based on that local main.
Local main was already one commit ahead of `origin/main`; it was not reset.

## Scope and confidence

Reviewed the proposal, all three iteration reports, presentation text, README,
data audit, UI tracker, information pages, repository layout, API routes,
critical service/ETL/model paths, frontend integration, dependencies, and deployment.
Ran offline Flask requests, captured 12 API response baselines, enumerated 30 API
routes, checked all 17 pages/assets, checked JavaScript syntax, and used Chromium
on all pages at 375px and 1440px. Browser requests used actual local historical
data; rankings were replaced with the local ranking snapshot and external
requests/images/fonts/icons were blocked. This is not a visual sign-off with
production fonts/images, a full interaction suite, or a cross-browser audit.

No production credentials were used to query providers. Production, account
settings, remote branch protection, Docker execution, multi-process load, full Git
history secret scanning, and third-party scraping permissions remain unverified.
An audit cannot prove the absence of additional defects. Findings below describe
verified behavior, source-level defects, or explicitly labelled risks.

Evidence: [baseline.json](audit/baseline.json),
[dependency-findings.json](audit/dependency-findings.json),
[browser.json](audit/browser.json), and `tests/fixtures/`.
Original documents are preserved in [history/](history/), including the notes
and presentation that were untracked at the beginning of this task.

## Immediate conclusions

1. The old Flask app exposes checkout files, including `.env` and `.git/HEAD`.
   Local GET requests returned 200. The restructure closes this boundary locally.
   If deployed with that configuration, treat provider credentials as exposed;
   rotate them and check deployment logs. Production exposure was not probed.
2. A tracked debug script contains a credential-like RapidAPI literal. The current
   file now reads the environment; the old literal remains in Git history.
   Rotation and any history cleanup require the repository/account operator.
3. Current probability outputs are unsuitable as coaching predictions. Training,
   inference, schemas, labels, formulas, and confidence claims have major defects.
4. Summary statistics themselves need correction before stronger models are built.
5. Reliable next-delivery data on a strict $0 budget is an unresolved feasibility
   gate. Replay and optional manual scoring must remain supported modes.

## Security and supply chain

| ID | Severity | Finding and evidence | State / ticket |
|---|---|---|---|
| SEC-01 | Critical | Original `Flask(static_folder='.')` plus root catch-all serves `.env`, Git metadata, Python source and data. Reproduced with test client without printing contents. | Closed locally by T000; production verification/rotation T001 |
| SEC-02 | Critical | Original `debug_rapidapi.py` contains a hardcoded credential; Git log shows it in earlier commits. No validity check attempted. | Literal removed locally; T001 |
| SEC-03 | High | Original HF workflow uploads `.` indiscriminately; Git ignores are not an upload allowlist. Original Docker copies checkout with no `.dockerignore`. Local secrets/venv/raw data could enter deployment contexts. | Allowlisted stage and `.dockerignore` added; T013 verifies actual release |
| SEC-04 | High | Original bootstrap inserts raw `json.dumps(match)` into a script: `</script>` in data can terminate the element. | Escaped locally and regression tested in T000 |
| SEC-05 | High | Remaining DOM sinks: `flagHtml` interpolates country into HTML/attributes; `resetMatchDetailPlaceholders` inserts team names into `innerHTML`; `esc` does not escape apostrophes although some inline handlers use single quotes. | Source-confirmed unsafe patterns; exploit chains need targeted tests. T003 |
| SEC-06 | High | Dependency audit reports 25 entries, deduplicated to 16 package/advisory pairs across seven packages: certifi, idna, requests, soupsieve, urllib3, Werkzeug, flask-cors. Exact versions/fixes are in evidence. | Open T002; no claim that all advisories are reachable |
| SEC-07 | Medium | CORS was enabled twice and explicitly set to `*` on all responses. CORS is not authentication/rate limiting. | Single API-only origin allowlist now; T003 reviews headers/CSP |
| SEC-08 | High | Anonymous requests trigger expensive disk parsing, ranking scrapes and provider calls. No application rate limiting or global request budget. Numeric limits are unbounded/negative. | Live calls now opt-in, body size bounded; T004/T005/T006/T025 |
| SEC-09 | Medium | `str(e)` is returned by several API endpoints. Provider exceptions may contain request URLs, IDs or implementation details. | Provider helper logs only exception type now; API cleanup T004/T014 |
| SEC-10 | High risk | Training code loads pickle from disk with no provenance/hash/version policy. Untrusted pickle can execute code. No remote model loading was observed in the running inference path. | T020; never accept public uploaded pickles |
| SEC-11 | Medium | No explicit CSP, full security-header policy, provider image URL validation, or HTML sink policy. Inline scripts/handlers complicate CSP enforcement. | Basic headers added; T003/T012 |
| SEC-12 | Medium | Old workflow used mutable action tag, broad upload and no checks. No branch protection is proven. | Checks and pinned checkout added; remote policy remains T013 |

## Backend, API, caching and performance

| ID | Severity | Finding and evidence | Ticket |
|---|---|---|---|
| API-01 | High | `/api/matches` serializes all 6,246 enriched historical matches with full scorecards: 43,110,285 response bytes and about 5.2s in one local sample. Browser pages request it repeatedly. | T005 |
| API-02 | High | `load_processed` reparses JSON on each request; completed match lookup scans a list. This contradicts the documented O(1), sub-200ms behavior. File size is 98,257,171 bytes. | T005/T006 |
| API-03 | High | `?limit=nope` yields 500 on players/leaderboard. `limit=-1` returns about 2.2MB of players rather than rejecting the request. Similar unchecked conversions occur on rankings/search. | T004 |
| API-04 | Medium | No uniform schema for errors, not-found, invalid format, metric, limits, request object shape, missing data, or readiness. A list/string JSON body can reach `.get()` in prediction POST. | T004 |
| API-05 | High | Disk cache writes are non-atomic, reads may race/see invalid JSON, locks/backoff are process-local, `_CACHE_LOCKS` grows with arbitrary IDs, scorecard daily gate is not atomic. | T006/T025 |
| API-06 | High | Redis TTL is treated as age zero whenever present and TTL was assumed to be 60 minutes. Expired Redis entries cannot provide stale fallback; workers do not share provider backoff/locks. | T006 |
| API-07 | High | Stale ranking lookup can execute 12 HTTP scrape combinations, retries and sleeps in a web request. This can exhaust the request timeout/free quotas. | T007 |
| API-08 | Medium | Missing API key was only checked against a placeholder literal, not empty string. Status can claim a key is set when empty. Redis connection success was printed without a ping. | Fetch guard fixed locally; health semantics T014 |
| API-09 | Medium | Live and historical match arrays are concatenated without canonical identity reconciliation or sorting/deduplication. Same real match can appear twice with different provider IDs. | T005/T017/T026 |
| API-10 | Medium | Detail rendering exists in both server bootstrap and JS, including raw historical fallback. Multiple ML/global handlers can initiate duplicate requests and update the same panel. | T012 |
| API-11 | Medium | No resource budgets, latency distribution, memory benchmark, structured request IDs, provider quota counters or useful readiness failure. Health returns `ok` even with missing data. | T014/T031 |
| API-12 | Medium | Factory/blueprints now exist, but `services/legacy.py` and `api/routes.py` deliberately retain large procedural modules; process backoff/raw-match cache still have shared state. | T006/T012; do not mistake file movement for full modularization |

## Cricket data and statistical integrity

Current measured coverage: 6,651 raw `.json` files (2,520 ODI, 3,254 T20, 877
Test), 6,246 processed matches, 4,812 players, 109 teams, 463 venues. Processed
match dates span 2002-06-27 to 2026-04-10. The older audit counted three more raw
files; do not carry those counts forward without checking what was counted.
The difference between raw and processed match counts needs an explicit exclusion
ledger, not an assumption of complete coverage. There are no duplicate IDs within
the processed historical list; that does not establish cross-provider uniqueness.

| ID | Severity | Finding and evidence | Ticket |
|---|---|---|---|
| DATA-01 | Critical | ETL explicitly approximates per-innings batting with per-match totals in `build_raw_accumulators`. Two Test innings can become one score, one innings and one dismissal. Highest score/milestones/averages/form are consequently unreliable. | T009 |
| DATA-02 | High | `is_wide_or_noball` is reused for batter balls faced; bowler-ball increment includes no-balls. Batter balls faced and legal bowling deliveries require different rules. | T009 |
| DATA-03 | High | Bowler conceded runs use delivery total, including byes/leg-byes. Bowler wicket credit uses exclusion lists rather than a validated dismissal contract; non-striker dismissals can be missed in batter state. | T009 |
| DATA-04 | High | Maiden tracking keys use bowler + over number without innings identity; over 0 can collide across Test innings. Best figures/innings wicket fields are not properly finalized by the shown accumulator. | T009 |
| DATA-05 | High | Draws are folded into H2H ties or team no-result, and first-innings-versus-chase logic is reused for Tests. Venue aggregates mix formats; T20 phase samples omit zero-run phases. | T009 |
| DATA-06 | High | Training expects `player -> year -> format`; generated yearly data is `player -> format -> year`. Inference reads that latter structure but other team/H2H/venue accesses do not match generated nesting. | T008/T010 |
| DATA-07 | Medium | Names are entity keys, countries inferred from first encountered team, no canonical provider mapping/venue alias history. Transfers, aliases and renamed venues are not represented safely. | T017 |
| DATA-08 | High | No immutable delivery table, schema versions, source hashes, rejected-file ledger, published/observed timestamps or reproducible data manifest. No incremental regeneration contract. | T015/T018 |
| DATA-09 | High | Historical coverage is a subset of men's internationals, not complete cricket history. 168 curated player profiles and 11 detailed venue profiles cannot represent full career or pitch coverage. | T011/T015 |
| DATA-10 | High | Cached fixtures/rankings can be old. Hardcoded April 2026 rankings get `scraped_at=now`; UI can imply current standings. Sample ICC calendars can resemble real upcoming fixtures. | T007/T011 |
| DATA-11 | High | Dropped catches/missed chances, pitch state, field placements, line/length, crowd reaction and psychology are not systematically observed. Weather/rain alone cannot prove pitch bounce or a player's mental state. | T021–T024 |
| DATA-12 | Medium | Git/LFS/manual upload policies conflict; claims about a universal Git 10MB limit and automated full live/historical parity are unsupported. No explicit data freshness/checksum/source build identity. | T013/T015 |

## ML and prediction validity

| ID | Severity | Finding and evidence | Ticket |
|---|---|---|---|
| ML-01 | Critical | Flask uses `ProbabilityEngine`, which computes heuristics; it does not load/use `CricketMLModels` saved models. Displayed ML accuracy does not describe the served system. | T008 |
| ML-02 | Critical | Batting labels are yearly mean runs/innings above a threshold, not whether the next innings reaches that milestone. Average is also an input, creating a closely related target/feature shortcut. | T008/T019/T020 |
| ML-03 | Critical | `model.score(X_scaled,y)` is measured on fitted data; no held-out temporal split, class-imbalance baseline, calibration, grouped matches or leakage audit. 97–99% is not predictive evidence. | T020 |
| ML-04 | Critical | `1 - stats.norm.sf(threshold,...)` is a CDF, reversing upper-tail interpretation. Arbitrary clipping can yield P(100+) > P(50+). Reproduced SC Cook/Test: century .70, fifty .516; SR>140 .80 at recent SR 41.05. | T008 |
| ML-05 | High | Confidence is an arbitrary function of yearly sample count; `_empty_probability` fabricates .5 for unknown data. A leaderboard evaluates only the first 100 names. | T008 |
| ML-06 | High | H2H lookup expects a different key format, venue lookup expects missing chasing/defending structures, percentage scales are inconsistent, and venue team-format nesting is ignored. | T008/T010 |
| ML-07 | High | Fixed probability clipping, all-format win ratios and omission of draw/tie/no-result cannot represent meaningful Test outcomes or live match state. | T008/T019 |
| ML-08 | High | Saved batting models share inference scaler state even though training creates separate scalers. No model card, artifact identity, reproducibility manifest or trusted load policy. | T020 |
| ML-09 | Critical gap | There is no next-delivery training target/state engine/model, online/offline feature parity or before-delivery prediction ledger. Current web predictions lack current striker/bowler/score/target state. | T018–T020/T026–T028 |
| ML-10 | High risk | Adding retrospective weather, final XI, media or post-ball incidents without availability timestamps will leak future information. More features do not establish improved performance. | T019/T021–T024/T030 |

## UI, UX, accessibility and frontend

Browser evidence has 34 completed page/width cases. No case showed document-level
horizontal overflow at either tested width. Several elements extend beyond the
viewport inside ticker/scrollable tables; this alone is not a defect. Manual
keyboard/touch checks are still needed to distinguish scrolling from clipping.

| ID | Severity | Finding and evidence | Ticket |
|---|---|---|---|
| UI-01 | High | Team profile emits `Cannot set properties of null (setting 'textContent')` at both widths. Source also contains `this.remove();this.parentElement.textContent=...` image fallback: parent is null after removal. External images were intentionally blocked during this audit. | T011 |
| UI-02 | High | Demo/static metrics, probability bars, venue narratives, selected-player defaults, and fallback rankings are not consistently distinguished from real data. Historical subset statistics are described as career/all-time. | T008/T011 |
| UI-03 | Medium | Static markup scan found an unlabelled input on every page, plus extra inputs on compare/list/search pages. Placeholder text alone is not an accessible label. | T011 |
| UI-04 | Medium | Nine `href='#'` links across matches/teams/venues, profile links without selected entity parameters, and action-like controls such as Follow require a behavior inventory. | T011 |
| UI-05 | Medium | Tab/focus/keyboard behavior, live-region announcements, contrast, reduced motion, touch target sizes and screen-reader tables are unverified. Test 320/375/768/1024/1440 widths, long names and all expanded tabs. | T011 |
| UI-06 | High | Charts/comparison verdicts and probabilities can be calculated differently in frontend and backend; summary verdict compares averages/runs without adequate context, uncertainty or sample size. | T008/T012/T029 |
| UI-07 | Medium | Multiple inline scripts/large per-page styles/global functions and duplicate initialization increase race/maintenance risk. Frontend API origin is hardcoded except localhost. | T012 |
| UI-08 | High | Live badges are not reliable freshness indicators; no prediction cutoff, source lag, revision state, model version or stale-data abstention. Cached scores cannot support claims of fresh next-ball forecasts. | T025–T028 |
| UI-09 | Medium | Third-party fonts/icons/flags/photos are required for full visual rendering. Complete offline visual operation is not proven. Missing-logo JS path was corrected during migration. | T011/T012 |
| UI-10 | Medium | No coach-specific scouting workflow, match preparation view, annotation workflow, accessibility acceptance suite, or user-validation evidence. | T029/T031 |

## Operations, cost and product constraints

- The original verification script prints success even after failures and does
  not assert HTTP/JSON contracts. Regression tests now exist, but coverage is a
  foundation rather than a complete acceptance suite (T010/T011/T013).
- There was no explicit upload boundary, data artifact registry, restore drill,
  rollback procedure, migration policy, multi-environment configuration or
  trustworthy release gate (T013/T015/T031).
- Free hosts sleeping, quota exhaustion, cache storage loss and browser worker
  resource costs are material to live prediction. No $0 architecture can promise
  worldwide always-on scoring with a guaranteed latency SLA. T016 must prove
  permitted and affordable access before T025 selects an adapter.
- Playwright is a collection/testing tool, not a data licence or a guarantee of
  low-latency feeds. No bypass of authentication, paywalls, CAPTCHAs or rate limits
  belongs in this plan. Provider terms/redistribution rights must be verified.
- No automatic paid fallback, metered API, GPU service, required credit card or
  paid LLM is approved. Local CPU training, bounded stored datasets, replay and
  manually scored sessions are the safe defaults.
- Authentication and privacy become necessary before storing private coach
  notes/rosters; they were outside the old MVP. Do not publish private tactical
  notes as global public JSON (T029).
- Being the best is a product ambition, not a measurable acceptance test. We will
  measure data correctness, calibration, prediction latency/coverage, operational
  cost, and whether coaches can complete useful workflows (T030/T031).

## What changed in T000

Added an application factory, API/web blueprints, restricted public-file serving,
app-scoped configuration/engine, path anchoring, assets/templates directories,
module-based pipeline/integration commands, WSGI entry point, static frontend
build, allowlisted backend staging, Docker ignore, basic headers, configurable
CORS and offline-by-default feeds. Escaped server bootstrap JSON, removed the
debug credential literal, and stopped logging provider exception URLs. Preserved
API analytical responses deliberately; this preserves existing statistical bugs
until the separate correctness tickets are implemented.

**Release is not ready:** T001 credential work, T002 dependency vulnerabilities,
T003 remaining DOM security, and T008/T009 statistical defects remain open. The
release workflow intentionally fails its vulnerability gate until T002 resolves
the findings. No remote deployment, push or account change was performed.
