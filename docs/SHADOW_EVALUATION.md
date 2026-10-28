# Prospective evaluation tooling and pending cohort

SHADOW_PROTOCOL.md was committed before this implementation as `0e3b5b0`.
Do not amend that frozen protocol after observing cohort outcomes. This ticket
implements the audit machinery; **no actual prospective cohort has started**.
`audit/prospective-shadow-2026-10-28.json` has null performance and a NO-GO decision.
`audit/shadow-tooling-fixture-2026-10-28.json` is a separately labelled virtual-clock
fixture, not measured live performance. Do not combine the two reports.

Build the fixed training-only empirical and phase/innings baselines privately:

```powershell
build/env312/Scripts/python.exe -m criclytics_app.ml.shadow_baselines --features build/features-v1-first --model build/baseline-v1-first/model.json --model-sha256 fe917b696bb25d2672b94f68e590fd665cdeed21ec06c55e23bafc1dda319beb --output build/shadow-baselines-v1-final.json
```

That fresh output already exists in this session. Retain it; a repeat needs a fresh
path. Its SHA256 is461043fd133601034a0a4421a7d43a0edf7c3a0f92ba0f428e08abfa30c65213.
Source feature-export hash, exact label vocabulary, training cutoff, dataset and
protocol hash are bound into it. The builder reads training rows only, with
additive-one prior and phase shrinkage20; no future cohort/test outcomes are read.
`audit/shadow-artifacts-2026-10-28.json` records those identities.

Explicit local `FORECAST_BASELINES` and `FORECAST_BASELINES_SHA256` configuration
add these two distributions and their protocol/artifact IDs to **new** issued
forecasts. Existing state/model ledger entries stay immutable; a missing historical
baseline is counted as missing rather than retrofitted. Public forecasting remains
unavailable, the optional API remains loopback/same-origin, and no collector is
enabled. A protocol change requires a new reviewed artifact and cohort.

T030 also adds bounded, idempotent decision records (state plus reason set) for
eligible/abstained states when a core exists. Unavailable source without a known
target cannot fabricate a target-level abstention. Raw observations, source quota
and prior issued payloads are unchanged. Older ledgers without decision data yield
an explicit unavailable breakdown. Schema initialization happens once per service;
current-state issued reads avoid repeated write transactions. An initial repeat
load check exceeded100ms reader p95; the fixed path measured about74ms p95 over
100reads/four threads, one inference, one source input. See the separate T030
resource report; it is not a hosted latency SLA.

Before any real enrolment, copy `shadow-cohort.example.json` to private storage.
It intentionally contains no matches. Bind the frozen model/baseline/protocol
hashes and actual freeze time. A match entry must have `match_id`, `mode: manual`,
`enrolled_at`, `rights_confirmed: true` and a `timing_review` object containing
reviewer, method and evidence_ref. Those are real review assertions/evidence, not
fields to fill with invented values. Enrol before the match's first attempt and
forecast and after artifact freeze. Keep review identity/evidence private.
Real ball-start timing and human/source completeness remain external requirements;
the CLI cannot prove physical timing merely from manually asserted timestamps.

Audit a declared cohort into a fresh private report:

```powershell
build/env312/Scripts/python.exe -m criclytics_app.ml.shadow_evaluation --source <private-event-store> --ledger <private-issued-ledger> --cohort <private-enrolment.json> --model build/baseline-v1-first/model.json --baselines build/shadow-baselines-v1-final.json --baseline-sha256 461043fd133601034a0a4421a7d43a0edf7c3a0f92ba0f428e08abfa30c65213 --output <fresh-private-report.json>
```

The auditor reads source and derived SQLite in snapshots, caps30matches and100,000
collected attempts, selects the first issued entry for each physical target and
retains replacement/missing/pending/correction counts. It rejects replay, equal/
late issue, unknown/changing actual start, wrong protocol/model/baseline, late
enrolment, deleted outcomes and unreviewed timing/rights. It reassembles features
from the original raw confirmation receipt and as-of revisions/metadata, checks
state/feature hashes and recomputes both learner and baseline probabilities.
Later corrected outcomes never rewrite the original forecast. Future missing
outcomes remain pending, not assumed successful.

Outputs include coherent joint log loss/Brier/ECE/bins, rare-event/phase/innings/
cold subgroups, match-cluster bootstrap intervals, training-prior drift, source
lag and collected-attempt coverage. Unknowns remain null. Failure categories can
overlap; do not sum them as mutually exclusive attempt counts. External source
completeness is unknown. Optional context families remain excluded with null
prospective benefit; a new family needs fresh preregistration and a new cohort.

Predeclared gates return NO-GO or REVIEW_REQUIRED; the tool cannot deploy or
promote automatically. Actual30-match/5,000-attempt evidence and a human review
are still required. All fixture metrics are labelled synthetic; no real coach,
human scoring latency, current calibration or live-source approval is inferred.

Validation:89unit tests (one optional skip), raw-receipt/feature replay, frozen
baseline issuance, strict/equal/unknown timing exclusions, analytic fixture loss,
missing denominator and empty-cohort nulls; authored end-to-end audit fixture.
No new network/provider/account/billing action or deployment. Disable baseline
configuration and experimental API to stop shadow issuance; keep source, decision
and issued ledgers for audit and backups.
