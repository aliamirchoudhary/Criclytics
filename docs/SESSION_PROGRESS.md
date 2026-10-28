# Autonomous execution — 2026-10-28

The user authorizes local commits only on newly created ticket branches, chained
from the previous ticket branch. No pushes, merges, rebases, resets, tags, PR/API
repository mutations or permanent global/Codex configuration changes are allowed.
The chain begins at the existing Cloudflare fix d8a0ad9 (itself based on dev
e4f7ab4). The final branch must be reviewed and merged into dev by the user.

T001 is waiting for provider-account rotations and HF inspection login; precise
steps are in AUTHENTICATION.md. Live keys exist locally but their values are not
displayed or treated as administrative credentials. HEAD-only containment results
are recorded without retrieving secret bodies. Production status is inconclusive.

T002 uses isolated environments and managed interpreters under ignored build/;
the original environment and historical/processed datasets are preserved.
Each ticket file/index will carry its verification evidence. Unmet external
acceptance criteria remain pending rather than being marked complete.

## Local ticket branch chain

| Ticket | Branch | Commit | Evidence/status |
|---|---|---|---|
| T001 | work/t001-containment | 9b8ad3a | Local containment instructions; provider rotations/production checks pending operator |
| T002 | work/t002-dependencies | 60c29d7 | Hash-locked patched dependencies; zero pip-audit advisories; isolated Python 3.11/3.12 checks |
| T003 | work/t003-dom-security | 6102e7c | Vendored sanitizer; adversarial browser checks; script CSP report-only pending T012 |
| T004 | work/t004-api-validation | dfe36be | Bounded inputs; structured redacted errors; 17 tests discovered, one optional skip |
| T005 | work/t005-match-summaries | See local branch tip | 12,708-byte default list (6,271 fixtures), stable pages; Chrome 375/1440 pagination/filter checks pass; 20 tests, one optional skip |

T005 measured cold/warm list latency ~2.59s/2.08s before repository caching.
No provider accounts, remote Git resources, or deployments were changed.
All tooling is local/free; no billing or card setup.

| T006 | work/t006-data-repositories | See local branch tip | App-isolated bounded snapshots/index; atomic timestamped cache; shared SQLite refresh lease; 25 tests (24 pass, one optional skip); opt-in historical regression suite also passes |

T006 evidence: docs/audit/repositories-2026-10-28.json. Warm list/detail 347/8.49ms;
~250MB working set, one processed parse. No source data regenerated or deleted.

| T007 | work/t007-source-provenance | See local branch tip | Cache-only ranking HTTP; conservative dates/stale labels; bounded offline import preserves partial categories; sample schedule publication disabled; 28 tests (27 pass, one skip); three browser label checks pass |

T007 does not enable any collector or claim ranking fallback is current/verified.
Network source selection remains T015/T016; provider account work remains pending.

| T008 | work/t008-prediction-containment | See local branch tip | All legacy predictions withdrawn, numeric probability/confidence null; archived engine blocked; 30 tests (29 pass, one skip); 12 Chrome unavailable-state cases pass with zero page errors |

Prediction math/schema mismatches are contained by withdrawal, not described as
validated estimates. T020/T027 must satisfy numeric invariants before release.

T009 in progress on work/t009-cricket-aggregation (base e8abb42): common innings
scorer + streaming versioned rebuild, hand rules and attributed 2024 final checks
implemented. Final full-corpus candidate is building under build/data-v2-verified;
original processed data remains selected. Found/fixed transient Windows reader
sharing denial during expanded checks. No remote writes/deployments.

| T009 | work/t009-cricket-aggregation | See local branch tip | 6,651/6,651 accepted, zero rejects; recovered 167 draws/175 no-results/63 ties; 4,834 observed players; original artifacts unchanged; hashes verified; 35 tests (34 pass, one skip) |

Verified candidate: build/data-v2-final; not promoted to serving. Full difference
report: docs/audit/aggregation-v2-2026-10-28.json; real-scorecard evidence alongside.
Earlier build/data-v2-smoke/full are development candidates; data-v2-verified was
interrupted during refinement and has no final manifest. Preserve these artifacts;
only data-v2-final is the verified T009 candidate. Added native Windows shared-delete
reads plus bounded exponential write retry after contention failed short retries.
