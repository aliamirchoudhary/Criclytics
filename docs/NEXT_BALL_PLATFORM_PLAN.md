# Next-ball cricket platform: implementation plan

The broader product/data/operations roadmap is now
[CRICKET_PLATFORM_MASTER_PLAN.md](CRICKET_PLATFORM_MASTER_PLAN.md), double-checked
in PLATFORM_PLAN_REVIEW.md. The probability contracts and earlier evidence below
remain applicable; T041-T054 extend the implementation sequence.

Owner vision reaffirmed 2026-10-29. Budget remains $0, no card, no metered fallback.
The distinctive product is contextual probability and match preparation. Scoring,
history and the interface support it. This plan extends, rather than replaces,
the completed T001–T033 foundations. Execute one ticket/branch at a time.

## Probability contract

Predict the next **delivery attempt**, including wides and no-balls, as a normalized
joint distribution over batter runs, extras, dismissal type and legality. A six
and a run-out need not be mutually exclusive. Batter and bowler views derive from
the SAME distribution; do not train contradictory percentages for each view.
Reserved OTHER mass stays explicit. Display lower/upper event-probability bounds
when OTHER prevents an exact six/wicket probability. Missing evidence is not 50%.

Separate three products: a live next-attempt forecast bound to a confirmed state;
a hypothetical player/bowler/venue scenario; and a full-innings score/threshold
forecast. They have different labels, training targets and evaluation. A historical
50+ innings frequency must never be presented as a current next-ball prediction.

## Context and evidence

| Family | Inputs | Availability/evaluation rule |
|---|---|---|
| Batter and bowler | Format-specific source-ID history, deliveries faced/bowled, dismissals, handedness where verified | Strictly prior completed matches; shrink sparse samples |
| Matchup | Batter vs bowler attempts, dismissals, scoring outcomes | Exact IDs; retain sample count; unseen matchup backs off |
| Current form | Last5/10 observed innings, duck/wicketless streaks, recency | As-of chronology; same-day availability unknown; do not infer emotional state |
| Match pressure proxies | Innings, wickets, phase, target, required rate, partnership, recent attempts | Before delivery only; distinguish sporting pressure proxies from psychology |
| Venue and rivalry | Ground, format, opposition pair, relative team strength | Date-bounded; do not equate nationality or rivalry with a causal advantage |
| Weather/surface | Observed rain, temperature, humidity, wind, covered pitch, dew, reported surface | Timestamped sources; weather–bounce direction is conditional, not a fixed rain penalty |
| Home/crowd | Verified home designation, venue, attributed crowd incident | Neutral venues explicit; never infer boos from location |
| Fielding/incidents | Dropped catch, reviewed LBW, missed chance, brawl annotation | Attributed event observed BEFORE target attempt; corrections retained |
| Captaincy/politics/media | Verifiable change/event and publication/observation times | Hypotheses only until labelled evidence, inter-rater checks and ablation support exist |

The existing T021–T024 ledgers and protocols are the extension points. Do not
manufacture labelled pressure/politics/weather effects to fill a UI. User-authored
assumptions can be retained as hypothetical notes; an unsupported assumption must
not silently change a probability. Optional context cannot block the core model.

## Model development

T034 adds a contextual probabilistic candidate trained on available men's T20I
deliveries. Learn conditional player, pair, venue, opposition, phase and recent-form
components with sparse-history shrinkage and calibrated mixture weights. Freeze
the protocol before inspecting its new chronological held-out evaluation. Compare
against global and phase baselines, report joint log loss/Brier/calibration and
whole-match uncertainty, and retain failures. Preserve T020 and its immutable
issued history. More features or a larger dataset do not establish improvement.

Serve a bounded scenario explorer with searchable player/bowler/venue choices,
joint outcomes, event bounds, context sample coverage and date scope. Scenarios
are experiments, not a live forecast. Promotion requires the existing prospective
shadow gates; hypothetical player totals need the separate T039 sequence target.

## Scores and live data

100 calls/day permits roughly one call every144seconds during a four-hour match,
before discovery, retries or a second match. A30-second cadence needs480 calls;
two concurrent matches need960. Redis reduces duplicate user requests but cannot
create new observations between provider calls or remove upstream lag.

T033 restores a provider-hosted free score widget for display. Its content is not
ingested, scraped or treated as prediction timing evidence. Playwright is useful
for UI tests and a permitted scheduled collector; it does not grant data rights,
remove rate limits or make a sleeping free host always available. Keep one shared
producer and shared quota, never one provider/browser poller per visitor.

T038 must establish rights, no-card/no-overage terms, event identifiers, actual
lag, completeness/corrections and stable actor confirmation before enabling an
external next-ball feed. Until then use authorized manual scoring/historical replay,
with distinct labels. No CAPTCHA/login bypass, undocumented restricted endpoints,
rotating accounts or fake referrers. Ordinary live score display can ship before
ball-by-ball predictive validity.

## Rankings

T036 implements provenance-bearing source snapshots, parser drift checks, atomic
last-good retention and explicit stale status. ICC terms currently permit personal
extracts and reserve commercial use; a local personal-use collector is different
from public redistribution permission. Do not publish scraped rankings as official
current data without an approved reuse basis. Preserve a last-good REAL snapshot,
never substitute fabricated old defaults. Actual dataset leaders remain available.

## System design on existing free resources

Cloudflare serves public static assets. Flask serves bounded read APIs, selected
immutable data/model versions and explicitly allowlisted media. Public requests
must never initiate provider collection, retraining or expensive full-corpus scans.
Use immutable snapshot identities, bounded read caches and conditional responses;
stamp observation time separately from browser refresh time. A shared collector
reserves quotas/leases, writes append-only events, reconciles corrections, and
issues one forecast per state/model BEFORE publication. Visitors read the same
issued result. Retain invalidation/history rather than rewriting old forecasts.

T035 measures local concurrent HTTP reads and memory, bounds cache entries and
expensive selectors, coalesces identical cold reads, and documents actual capacity.
Use existing SQLite coordination without requiring the deleted Redis resource;
Redis can be optional after owner restoration. No claim of unlimited users or an
SLA on free sleeping/ephemeral hosts. Private coaching notes stay outside public
caches. No long-lived SSE connection per visitor on a two-thread WSGI process.

## Execution order and acceptance

| Ticket | Deliverable | Release/evidence gate |
|---|---|---|
| T033 | Original-site parity audit and usable cricket workflows | Actual browser interactions, photos/source review, strict CSP, tests |
| T034 | Contextual candidate and what-if probability explorer | Frozen protocol, held-out metrics, calibrated coherent outputs, leakage tests |
| T035 | Shared read serving and measured concurrent capacity | Cold/warm concurrency, bounded resources, zero provider calls from readers |
| T036 | Real-source ranking import and retained backup | Rights scope, dated source, parser checks, last-good/stale tests |
| T037 | Context availability/annotation workflow | Attribution, pre-attempt timing, missing/conflict handling, no invented effects |
| T038 | Timely authorized delivery source | Actual lag/coverage/correction trial within $0 and source rights |
| T039 | Player-innings/team outcome model | Separate target/protocol, temporal calibration, sequence evaluation |
| T040 | Coach validation and release | Real user feedback, prospective gates, credential containment and reviewed main |

Operator/source-access dependencies may leave a ticket blocked; continue independent
work instead of inventing evidence. Local commits on new chained ticket branches
are authorized; pushes, merges and publication still require explicit approval.
