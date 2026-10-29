# Cricket platform master plan - 2026-10-29

Owner requirement: one place for following cricket, exploring its history, asking
questions, preparing teams, broadcasting rivalry stories and evaluating future
outcomes. Prediction is a central product, supported by dependable data and useful
workflows. This supersedes the scope of NEXT_BALL_PLATFORM_PLAN.md without erasing
its model contracts or completed tickets. Budget is permanently $0/no card unless
the owner changes it. Planning is complete before T041 implementation; review is
in PLATFORM_PLAN_REVIEW.md. Implement one bounded ticket/branch at a time.

## Product and measurable success

| Audience | Workflow | Acceptance |
|---|---|---|
| Fan | Follow current match, upcoming fixtures, scorecard, player entry and key events | One-click match access, visible source age, correction handling; never false live status |
| Historian/fan | Find an old match, innings, spell or rivalry, filter by opponent/venue/format/date | Stable links, complete supported scorecards, source dates, coverage and exclusions |
| Coach | Match preparation, batter/bowler scenarios, opposition plans, role-balanced XI | Searchable choices, explainable samples/uncertainty, explicit assumptions and private notes |
| Selector | Recent and long-term role-adjusted comparisons, workload, team fit | Evidence-based shortlist, configurable constraints, no invented fitness/nationality or automatic selection claim |
| Analyst/broadcaster | Rivalry dossier, venue trends, milestone/record queries, shareable evidence cards | Deterministic reproducible facts with dates/sources, exports and clear sample scope |
| Prediction user | Pre-match result, player terminal-score, next-attempt distribution | Separate validated targets, coherent probabilities, as-of data, calibration and abstention |

Publish aggregate performance and failure cases. No promises of certain outcomes,
profit, betting signals or coaching effectiveness unsupported by evaluation.
Coverage expands explicitly: men's international T20I first for predictive work;
history can cover ODI/Test, then women/domestic by separate schema/evaluation gates.
Never label available matches as complete careers or all cricket history.

## Can scraping solve the source problem?

Yes, a permitted HTML/Playwright collector is a valid adapter. Review each SOURCE,
not the tool: rights to collect/display/cache/train, robots, authentication,
request limits, IDs, source delay and corrections. Prefer documented downloads/API
over browser rendering. Use one central scheduled producer, never one per user.
No stealth browsers, forged identity, account rotation, CAPTCHA or restriction bypass.

Google Search is not the scheduled feed: its robots disallow /search, and its
terms prohibit automated access contrary to machine-readable instructions. A
search score is also an aggregation with no established delivery timing or next
participant contract. Human discovery of a source differs from an automated Google
poller. Displayed scores alone do not prove a next-ball prediction preceded that
ball. T045 investigates direct sources without silently granting ingestion rights.

ICC rankings can be parsed (T036 already proves that locally). Scheduling is easy;
public reuse permission is a separate outstanding issue. Player tables update
weekly (women Tuesday, men Wednesday), team tables after Test series/ODI/T20I;
monthly is too stale. Proposed checks: players weekly after publication, teams
daily only when relevant fixtures completed, conditional requests and last-good.
No hardcoded ratings or another website's copy as a rights workaround.

## Source and refresh plan

| Data | Candidate/source | Cadence and policy |
|---|---|---|
| Historical deliveries/scorecards | Cricsheet JSON, ODC-BY1.0; official archive links | Daily bounded conditional refresh; authoritative complete archive reconciliation handles corrections/withheld matches; no manual monthly copying |
| People/venue identity bridge | Cricsheet Register; Wikidata CC0 | Weekly change detection, exact source-ID joins; ambiguous merges go to review |
| Fixtures/live attempts | Direct permitted provider/site, official embed for display; manual/replay retained | Discover near match windows, one global poll/lease, provider-aware backoff; actual lag/rights trial before live forecasts |
| Weather forecast | MET Norway Locationforecast; Open-Meteo only within qualifying free service terms | Per venue, respect Expires/Last-Modified, shared across users; retain each issued forecast/run and receive time |
| Venue geography/home designation | Sourced register/Wikidata plus attributed affiliation records | Versioned changes, neutral explicit; never infer boos or bounce from geography |
| Pitch/ball conditions | Attributed reports/instruments/manual labels with reuse basis | Before relevant attempt, independent tags versus actual measurements |
| Fielding/crowd/captaincy | Structured attributed observations/official factual announcements | Event-triggered revisions, reviewers, confidence/unknown, prior-attempt cutoff |
| News/media | Permitted RSS/official releases, links and attributed factual events | Low cadence, preserve publication/observation; no article copying or unverified politics/mental-state labels |
| Rankings | ICC or another source with a documented public reuse basis | Category-aware conditional schedule; original effective date, current+backup and parser drift checks |
| Player photos | Wikidata identity -> Commons image, verified CC/PD/CC0 Flickr or owner-contributed media | Metadata first, per-file licence/identity/attribution, cached download, bounded concurrency; stop429/Retry-After |

Cricsheet refresh improves post-match history/form; it is not live scoring. Record
actual receipt time, provider publication if known, event time precision and source
revision separately. A historical weather reanalysis is not an as-issued forecast.
A full archive's removed matches must not reappear by merging old retained raw files.
Retain withdrawal audit hashes privately, exclude withdrawn data from active marts.

## One data platform: modest medallion architecture

Use logical bronze/silver/gold layers on existing files/SQLite first. Parquet plus
DuckDB can be added for measured offline analytical needs; no Spark cluster,
Databricks, paid warehouse, hosted vector store or new paid infrastructure.

Bronze: immutable original ZIP/JSON/HTML/forecast/media responses, checksums, source
licence/terms, fetch/issue/effective times and ingestion runs. Never public static.
Silver: canonical match/innings/attempt/person/team/venue/competition entities,
exact identity bridges, ordered event revisions, weather runs and context records.
Use one schema registry, explicit units/timezones, stable IDs and tombstones.
Gold: versioned match/scorecard, player/role/form, venue, rivalry, record/search
marts, serving shards and offline/online feature snapshots. Public gold contains
permitted derived facts; private coach information is a separate access domain.

Core tables: sources, ingestion_runs, observations, entity_links, matches, innings,
delivery_revisions, player_appearances, forecasts_weather, venue_affiliations,
context_annotations, ranking_snapshots, media_licences, dataset_versions,
feature_snapshots, model_versions, issued_predictions and later settlements.
Every derived row can identify input observation hashes and transformation version.

Flow: schedule -> reserve lease/budget -> fetch conditional -> archive -> validate/
quarantine -> normalize/resolve IDs -> quality/difference gates -> build immutable
gold -> publish manifest atomically -> readers select one version. Never partial
overwrite. Independent model job -> frozen evaluation -> candidate registry ->
promotion gates. Never retrain on a visitor request or auto-promote every new fit.

Full source reconciliation is authoritative for its declared scope. New deliveries
must not remove other formats; combined manifests list all required partitions.
Missing/schema-drift/coverage collapse/corrupt download fails the run and retains
last good selection. A successful fetch is not a successful website refresh.

## ML and runtime feature contract

One feature definition shared by training, replay and runtime. Each feature has
type/unit/entity/format/window, source/availability, missingness, maximum age,
transformation version and model compatibility. Fit encoders and history on prior
data only; use chronological whole-match partitions and fresh untouched cohorts.

First add exact match state: innings, legal attempts, runs/wickets, batting order,
striker/non-striker/bowler, target/required rate where applicable, phase, recent
dot/boundary/wicket sequence, partnership and pre-attempt score changes. Strong
history includes opponent-adjusted role/form, last5/10/20 observed innings with
recency/sample counts, batter-bowler pair and venue/competition strength.

Pressure PROXIES can be objective: required-rate gap, wickets remaining, chase
leverage, tournament stage, knockout/final designation, recent low scores, dot
streak and recorded prior chances. None establishes an emotional state. Crowd,
captaincy/media incidents and hypothetical pressure need attributed timing and
labels. Optional unsupported features remain masked, not assigned invented
coefficients. Rain never maps mechanically to less bounce. Evaluate ablations,
missingness robustness and subgroup calibration before enabling a family.

Targets: coherent next-attempt joint distribution; player continuation/terminal
score and thresholds; pre-match and in-match joint result. Test/ODI/T20/women/
domestic populations require separate applicability contracts. Start with CPU
smoothed models and well-calibrated tabular candidates; compare stronger CPU
boosting/sequence/survival approaches only against frozen baselines. Dataset
volume or a complex model is not acceptance. Retain losses as well as wins.

At runtime, consume a confirmed reconciled state and eligible context snapshot,
check freshness/actors/model scope, compute once per state/model version, store
immutable issue time, publish to readers, then settle against later truth. Stale,
gap, pending correction, unknown actors or observed target -> no current forecast.
Monitor log loss/Brier/calibration, availability, coverage and issue-before-target,
not misleading raw accuracy. T034/T039 remain frozen references; don't retune them.

## Queries, selection and storytelling

Create a structured query service over gold: entity autocomplete, match/innings/
spell search, date/format/opponent/venue/phase/threshold filters, role-aware
comparisons and rivalry dossiers. Support question templates such as best innings
in successful chases, player against a bowler at a ground, opposition phase scoring,
and before-match rivalry history. Every answer identifies descriptive/forecast/
hypothetical status and data cutoff. No expensive arbitrary public SQL.

Natural-language convenience starts with a bounded local intent/entity parser
and explicit clarification choices. Core functions need no paid LLM or inference
provider quota. Unknown questions offer searchable structured options. Later local
models are optional and cannot fabricate facts. Coach XI tools use role, workload,
availability and eligibility constraints, show tradeoffs and uncertainty, and keep
private rosters/plans off public caches. Broadcaster exports are sourced fact cards,
not scraped article summaries or invented rivalry drama.

## UI/UX and capacity

Keep the current original-inspired blue interface available for owner review.
Primary journeys: Live/Matches, Explore history, Players, Compare, Predictions,
Team lab, Rivalry/Media desk. Prefer visible search/cards/chips and useful defaults;
progressively reveal specialist controls. A compact live banner links one match
centre with scorecard, timeline, context, prediction and evidence. Images use
local thumbnails/srcset/crop/credits and honest initials fallback; flags stay local.
Mobile and keyboard states, slow/offline/empty/error/correction states are acceptance.

Serve static pages and permitted immutable gold shards through Cloudflare's CDN;
paginate/split each file below25MiB. Keep mutable latest pointers small and cache
conservatively. Existing Flask remains bounded dynamic scenario/read service.
Public read caching/singleflight already exists. Producer queues, snapshots and
local SQLite/WAL coordination precede optional Redis. Deleted Redis is not restored;
any new service needs verified free/no-card limits. Private notes initially remain
local/exportable; server persistence requires authentication/ownership isolation.

Thousands of visitors viewing static history is different from thousands polling
live JSON. At1,000viewers/30seconds,4hours needs480,000viewer reads even with one
upstream producer. Workers Free script requests currently cap at100,000/day; a
cache hit inside a Worker is not a free unlimited request. Plan separate CDN
immutable history, adaptive visible-tab polling, ETags/jitter, bounded live audience,
load shedding and genuine hosted measurements. No invented $0 unlimited live SLA.
Provider widget traffic is handled by that provider, not a predictive-feed loophole.

## Scheduling, storage, operations and rollout

Use standard public-repository GitHub Actions for bounded batch candidates after
approved integration; private/billable/larger runners disabled. Schedule off the
hour with concurrency lock, hard timeout, failure summaries and idempotent retry.
GitHub schedules may delay/drop and disable after inactivity: health/freshness is
explicit, no claim of always-on live collection. A local scheduler can run the
same CLI. No automatic Git commit/push or application/model release from these jobs.

Actions artifacts/caches have storage quotas and are not a durable warehouse.
Initial T041 produces local complete candidates and a read-only scheduled build
definition without artifact upload. T042 must establish a verified $0 durable
artifact channel, retention/size quotas, restore and signed/hash-pinned read-only
publication; it must not rely on cache retention or repo commits as a database.
Existing HF/Cloudflare resources may be used only within verified rights/quotas
and the owner's Git/release boundary. No R2/card/billing activation assumed.

Data cadence and model cadence differ. Daily data jobs can succeed while the
serving model remains the last evaluated version. Candidate retraining weekly or
on sufficient new data; time/memory bounded, evaluation/calibration/drift gates,
human/prospective promotion where required. Maintain data/model cutoffs visibly.
Monitor ingestion lag, quality/rejection/removal drift, identity conflicts, source
quota, storage, API p95/RSS/cache, model coverage/calibration and per-state reuse.

## Sequenced implementation

T041 automated authoritative Cricsheet ingestion/candidate job -> T042 durable
publication and scheduler health -> T043 canonical multi-source lake/identity
contracts -> T044 licensed media enrichment -> T045 direct live-source trials ->
T046 weather/competition/context acquisition -> T047 exact-state feature parity ->
T048 fresh candidate training/evaluation -> T049 search/history/rivalry desk ->
T050 coach/selector team lab -> T051 category-aware ranking/news automation ->
T052 integrated UX/mobile acceptance -> T053 hosted capacity/security/operations ->
T054 prospective coach/analyst pilot and reviewed release. Independent work may
proceed around external source blockers; dependent forecasts cannot bypass them.
Each ticket records exact acceptance, $0 resource budget, tests and rollback.

### Primary references checked2026-10-29

- Cricsheet downloads/licensing: https://cricsheet.org/downloads/ and https://cricsheet.org/licensing/
- ODC-BY1.0: https://opendatacommons.org/licenses/by/1-0/
- ICC frequency/terms: https://www.icc-cricket.com/rankings/faqs and https://www.icc-cricket.com/news/icc-website-terms-of-use
- Google: https://www.google.com/robots.txt and https://policies.google.com/terms
- Weather: https://api.met.no/doc/TermsOfService and https://open-meteo.com/en/terms
- Media: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia and https://www.wikidata.org/wiki/Wikidata:Licensing
- API etiquette: https://www.mediawiki.org/wiki/API:Etiquette
- GitHub billing/schedule: https://docs.github.com/en/billing/concepts/product-billing/github-actions and https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Cloudflare: https://developers.cloudflare.com/workers/platform/limits/ and https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
