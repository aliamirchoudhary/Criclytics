# Product plan: trustworthy cricket intelligence on $0

## Product outcome

Help a coach prepare for opponents, understand a live match, compare possible
actions, and review the evidence afterward. A next-delivery forecast must show a
distribution of outcomes, available context, uncertainty, model identity and the
exact score state at which it was issued. History must be correct before it is
used to train a model. A precise-looking percentage is not a useful outcome by
itself.

Begin with men's T20 internationals because the local corpus and phase structure
are manageable. Preserve existing ODI/Test browsing while correcting summaries;
add evaluated ODI/Test models later as distinct releases. Do not pool formats or
claim worldwide coverage by default. Women's/domestic expansion is a separate
data/evaluation decision rather than a hidden promise of the first model.

## Delivery sequence and gates

| Phase | Tickets | Exit evidence |
|---|---|---|
| 0: Contain and structure | T000–T004, T008 | Private files blocked, credentials addressed by operator, dependency/DOM risks fixed, invalid requests controlled, unvalidated forecasts clearly unavailable/labelled |
| 1: Reliable history and UX | T005–T015 | Correct innings/ball statistics, versioned fixtures, bounded API payloads, honest freshness/coverage, accessible core interactions and reliable release artifacts |
| 2: Data and access feasibility | T016–T019 | Permitted $0 source decision, stable identities, canonical deliveries, deterministic replay and strictly before-delivery features |
| 3: Measured baseline | T020 | Reproducible CPU model beats predeclared empirical baselines on untouched future matches with calibration/leakage reports |
| 4: Live pipeline | T025–T028 | Single bounded collector, freshness/correction handling, training-serving parity, forecasts issued before the event, abstention when stale |
| 5: Context and coach value | T021–T024, T029–T031 | Context survives ablations, private/public boundaries work, coach tasks tested, prospective shadow evaluation passes release gates |

Tickets form a dependency graph, not a promise that every later feature must wait
for every optional research experiment. One agent implements one ready ticket at
a time; operator work such as key rotation can remain explicitly pending without
stalling unrelated local repairs. T024 media/crowd research is optional and must
not block the baseline or launch.

## Prediction definition

The first target is the **next recorded delivery**, including wides/no-balls.
Predict a coherent joint outcome or factorization covering batter runs, extras,
total runs and dismissal event/type. A wicket can coincide with runs or an illegal
delivery; avoid an exclusive `0,1,2,3,4,6,wicket` label that discards these cases.
Keep bowler-attributed wickets separate from any dismissal. Clarify whether a
user requests the next attempt or the next legal ball; do not silently equate
them. Model rare outcomes explicitly or with documented pooling. No delivery
forecast is issued after an innings/match ends.

Compare empirical phase/format frequencies and smoothed batter/bowler baselines
before multinomial/logistic or CPU tree models. Use out-of-time match-grouped
splits, training-only transformations, a separate calibration period and untouched
test matches. Score log loss, Brier score, calibration, rare-event precision/recall,
coverage, subgroup drift and abstention. Report intervals clustered by match.
Accuracy alone is inadequate. Require a predeclared material improvement and no
unacceptable subgroup regressions; do not invent a target accuracy before a valid
dataset/baseline exists.

Persist issued predictions immutably with model version, source state revision,
feature snapshot/hash, issue time, event cutoff and eventual aligned outcome.
Corrections must not rewrite historical forecasts to make evaluation look better.
Backtesting and prospective shadow evaluation are separate evidence.

## Context inventory

| Factor | What can be measured | Initial treatment |
|---|---|---|
| Batter/bowler history | Previous deliveries, handedness/style where sourced, venue/opposition splits | Smoothed as-of statistics, cold-start priors, matchup sample sizes |
| Recent low scores/form | Prior innings and rolling ball windows | Time-decayed history; no future innings or completed-season aggregates |
| Match pressure | Required rate, target, wickets, balls remaining, dot streak, partnership | Observable state features; do not label inferred anxiety as fact |
| Home conditions | Venue, team, travel/home/away definitions | Explicit mappings; historical advantage is associative |
| Heat/cold/humidity/wind | Venue/time weather; prior exposure only where available | Timestamped forecast/observation with resolution and missingness; no nationality stereotype |
| Rain/dew/ball condition | Rain interruptions, announced ball changes, direct observations | Uncertain context; rainfall alone does not establish bounce or ball state |
| Pitch/bounce/pace/spin | Curated pitch reports, observed delivery proxies, match progression | Separate reported from observed; no invented tracking/line-length data |
| Playing XI/batting role | Announced XI, striker, non-striker, bowler, role history | Availability-time gated, format-specific IDs; substitutions handled |
| Dropped catch/misfield | Structured official event or attributed manual annotation | Provenance, confidence, event ordering; missing means unknown, not no drop |
| Brawl/booing/crowd | Verified timestamped observations, potentially manual | Optional hypothesis; no fabricated psychological ground truth |
| Media criticism | Licensed timestamped public sources, if obtainable at $0 | Research-only; no default causal/personality/mental-health inference |
| Injury/fatigue/fitness | Public confirmed reports or athlete-provided private data | Optional and access-controlled; do not infer hidden medical conditions |
| Field placement/tactics | Authorized manual inputs or licensed feeds | Optional scenario inputs; never claim they are in Cricsheet when absent |

Every feature needs event time, observed/published time, source, confidence,
licence, missing-value meaning and a training/serving availability rule. A feature
may be scientifically plausible yet unavailable or unhelpful. Run ablations for
each new family; exclude it from the production model if it adds leakage,
instability, unacceptable cost or no demonstrated value.

## $0 architecture and source decisions

- Local CPU processing/training comes first. Start with bounded files and SQLite
  where transactions/indexes are needed; no compulsory hosted database/broker.
- Historical Cricsheet data and its register are candidate foundations. Preserve
  per-source licensing/attribution and IDs. The [JSON specification](https://cricsheet.org/format/json/)
  and [register](https://cricsheet.org/register/) define the relevant structures;
  the register has its own published licence, separate from match data.
- [Open-Meteo's free service](https://open-meteo.com/en/pricing) is a candidate for
  non-commercial experiments: current published limits include 10,000 daily calls
  and no uptime guarantee. [Its site](https://open-meteo.com/) advertises no required
  API key/card. Check exact endpoint/archive/usage terms in T021; this is not
  blanket approval for commercial coaching redistribution or all historical data.
- [Free HF Spaces sleep when unused](https://huggingface.co/docs/hub/spaces-overview).
  Use cold-start-aware/replay operation; do not use artificial traffic to evade
  platform restrictions. Existing free account resources must be verified before
  allocating new services.
- Cache once per match/source, serve many users from that state, enforce daily and
  per-minute hard budgets, and stop before quota exhaustion. No provider request
  should be triggered independently for every website visitor.
- Evaluate permitted APIs, explicitly allowed public feeds and manual scoring.
  [Playwright](https://playwright.dev/python/docs/library) can automate a permitted
  source or test the UI. It cannot guarantee redistribution permission, provider
  latency, stable selectors, or an always-running free worker.
- If no legal, sufficiently timely, free feed exists, release replay/scouting and
  manual-scored match mode. Display the coverage/latency limit and continue the
  source search; do not call stale snapshots live predictions.

No subscriptions, trials that need a card, paid inference, hidden metered usage,
unbounded storage or auto-upgrade path are allowed. Recheck limits before each
service decision; record date and links in the source registry. The above links
were consulted on 2026-10-25 and are not permanent price guarantees.

## Coach-facing workflows

Start with opponent scouting by format, player/bowler matchup sample sizes,
venue context, recent form and downloadable attributed reports. Then add a live
match workspace showing score freshness, striker/bowler state and calibrated
next-delivery distributions. Allow structured coach annotations and clearly
marked what-if inputs. Scenario probabilities do not prove that an action causes
the predicted improvement.

Private notes/rosters require identity, ownership checks and reliable storage or
an explicit local-only export workflow. Do not build fake persistence on ephemeral
free storage. Validate with coaches/players on concrete tasks: locate an opponent
weakness, prepare a bowling plan with evidence, recognize a stale forecast, and
review an issued forecast after a match. Record feedback before expanding scope.

## Release acceptance

T031 must show: zero unresolved critical/high exploitable security findings or an
explicit operator risk decision; validated cricket golden fixtures; bounded API
payloads; core browser/keyboard flows; source rights and $0 quotas; reproducible
model/data cards; chronological and prospective calibration reports; stale-data
abstention; tested restore/rollback; and coach usability evidence. Aspirational
global reach and unsupported accuracy claims are never substitutes for evidence.
