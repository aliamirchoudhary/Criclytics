# Current platform handoff - 2026-10-29

The original blue cricket experience has been audited/restored and extended with
a real contextual what-if candidate. This is a local research platform, not a
released, proven next-ball coaching service. All work remains $0/no card.

Local preview: http://127.0.0.1:5050; explorer:
http://127.0.0.1:5050/workspace.html?view=scenario. The ignored launcher
build/t033-preview/run.py selects corrected data, private models, replay and
personal media/rankings. It does not restart the original replay producer.
If stopped, run it with build/env312/Scripts/python.exe from this checkout.
This is local only. No new deployment/public deployment URL.

## Implementation and acceptance

| Ticket | Local result | Remaining acceptance |
|---|---|---|
| T033 | Original-page audit, blue sports UI, card/search/button workflows, Probability/ML tabs, replay discovery,37configured photo identities and isolated live display | User visual review; provider originals stay private/personal |
| T034 | Coherent calibrated next-attempt candidate and player/bowler/ground explorer, shared POVs, samples/form dates/OTHER bounds | Prospective validation, current-data refresh, review |
| T035 | Bounded historical LRU/singleflight/ETags, query limits, measured concurrency | Hosted capacity/uptime observations |
| T036 | Real dated local ICC T20I batting/team import, strict parser, atomic retained backup, private/public boundary | Public automated reuse basis; remaining categories/formats |
| T037 | Attributed weather/captaincy/crowd/fielding import and as-issued coverage; hypotheses separate | Real observations, source rights, reviewer agreement, ablation |
| T038 | Verified source timing/rights/quota review and trial gates | Blocked: no approved free timely machine-readable feed |
| T039 | Separate sequence-derived terminal-score and joint match-result candidates; actual evidence visible in ML panels | No clear player gain; worse match calibration; continuation/prospective work |
| T040 | Fresh offline release/build/containment/restore checks | Blocked: coaches/prospective trial, rotations/containment, reviewed release |

Next-attempt held-out log loss1.78202 versus phase1.78925 on846test matches:
a modest retrospective improvement, not a six/wicket hit-rate guarantee. Exact
pair coverage is sparse. Form is the last observed5matches, not current inferred
mental state. Raw scope ends2026-04-09: old evidence by October. A versioned,
rights-checked current-data refresh and new frozen evaluation are needed before
claiming current form. Preserve the frozen models/reports; do not tune their tests.

Rain/bounce, crowd, boos/brawls, captaincy and politics are not fitted causal
effects. Exact chase/score/wickets and continuation dynamics need a new protocol.
Private hypotheses never change probabilities. Player-score candidate has no
clear extra loss gain over entry state; match candidate's calibration worsens
despite better log loss. Neither is promoted.

## Verification

103tests:102pass/one optional legacy skip. Python compilation/changed JS syntax
pass.13original processed hashes preserved. Clean19page frontend/backend builds,
private path denial, strict CSP and authored SQLite/dataset restore drills pass.
Fresh locked audit:31packages,zero known advisories, not proof of no app defects.

Browser evidence: original17page types/interaction states;95local page-width cases
and four failure/keyboard states;375/1440restored flows, scenario calculation/shared
POV/context-change clearing, real dated ranking tables/empty category, research
tables and isolated external widget. Chrome only, no screen-reader or hosted SLA.
See docs/audit/*2026-10-29.json, including the final matrix/preflight reports.

Local HTTP:200requests/100concurrent clients/two app slots,zero errors/provider
calls,four computations,196hits,warm p95~445ms. Not hosted/free-tier certification.
T034 training peaked~596MB; isolated loaded inference process~76MB. Train offline.

References: NEXT_BALL_PLATFORM_PLAN.md, ORIGINAL_UI_PARITY.md,
CONTEXTUAL_MODEL_CARD.md, PUBLIC_READ_CAPACITY.md, RANKING_SNAPSHOTS.md,
CONTEXT_AVAILABILITY.md, LIVE_SOURCE_ACCEPTANCE.md, INNINGS_OUTCOME_MODEL_CARD.md.

## Git and preserved resources

All local commits use aliamirchoudhary <aliamirchoudhary@gmail.com>.

| Chained branch | Implementation commit |
|---|---|
| feat/t033-cricket-workflows | e973f8f |
| feat/t034-contextual-model | 0e40637; protocol bb9f496 |
| feat/t035-shared-read-capacity | 054c0a5 |
| feat/t036-ranking-snapshots | ff4c16c |
| feat/t037-context-availability | f4c23d2 |
| chore/t038-live-source-gate | 5332742 |
| feat/t039-innings-outcomes | 4e331b1; protocol f70e8e9 |
| chore/t040-reviewed-release-gates | Local HEAD after handoff commit |

No push, merge, rebase, reset, tag, PR/remote mutation or deployment. Publication/
integration requires user approval. No commits on dev/main/pre-existing branches.

Preserve ignored build/contextual-v1-full, build/innings-outcomes-v1-full,
build/t033-player-media, build/t036-rankings.sqlite3, corrected data/identity stores
and build/working-preview-20261028-234643 replay/issued ledger. Raw/original data
preserved; deleted Redis not restored. Provider image originals remain outside
static output/Git. No tokens or secret settings are recorded here.

Next useful work: owner UX review, versioned current-data refresh, a new protocol
for exact match-state/continuation, then independent evaluation. Live ML still
requires source rights and measured before-ball timing. A displayed iframe is
not that feed. Credential/containment and real coach review are external release
work; no human review, source trial or prospective match was invented.
