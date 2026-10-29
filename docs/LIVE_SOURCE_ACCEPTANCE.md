# Timely delivery source gate (T038, checked2026-10-29)

No external next-delivery collector is approved. The policy remains replay/manual
only. This is an external evidence gap, not solved by a different scraping tool.
Existing scorecards, local replay, manual confirmation and opt-in external live
display remain available. No provider trial or credential-consuming benchmark was
run without an approved source basis. Actual external lag/correction values remain
null, not a guessed delay.

[CricketData pricing](https://cricketdata.org/pricing/) states no credit card is
needed,100daily free hits and data a few minutes behind real time. For one4hour
match,30second polls require480calls;100calls permit144second spacing even before
discovery, scorecard/details, retries or another match. Redis/shared scheduling
removes duplicate user calls; it cannot remove the source delay or this arithmetic.
The existing SQLite global budget/leases can safely share a delayed scoreboard
once reuse is approved, but cannot establish a next-ball forecast before the ball.

[CricTimes widget](https://crictimes.org/live-cricket-score-widget) supports free
embedding and an official custom builder. Ordinary Chrome confirmed real score
content in the isolated opt-in frame. Display permission is not a machine-readable
delivery-feed licence; no widget DOM/API extraction, request interception or
cross-origin bypass is enabled. Its latency/coverage/correction guarantees are
unknown. Browser automation does not grant missing rights or quota. The failed
CricketData widget/referrer trial was stopped, not bypassed.

Before approving a source, retain a dated primary-source rights/limits record:

1. Explicit collection, caching, public display/redistribution and ML/derived-use
   basis for this project; rate limits/robots/attribution and retention rules.
2. Permanent free/no-card access; no overage, billing activation, account rotation,
   duplicate accounts, paid fallback or workaround for blocked access.
3. Stable match/player/event IDs, delivery attempts including illegal balls,
   source revisions/corrections, match status and confirmed next participants.
4. Observed full-match trial, including pauses/wickets/over changes and at least
   one correction where available. Record absent corrections as untested, not pass.
5. Independently observed event times versus platform receive/confirmation/issue
   times. Retain p50/p95/max lag, missing/reordered/duplicate attempts and target
   opportunities closed before a forecast could issue. Never infer independent
   event time from the same delayed feed being assessed.
6. State-validity and no-peek gates from T026/T027: forecast issued before target
   observation, actor confirmation not expired, no pending correction/gap/stale
   state; immutable issued history and invalidation. One producer/result per state,
   visitor reads only. No per-user polling of upstream services.

Use local manual scoring as an explicit shadow mode during independent trials.
A human can confirm a next striker/bowler; this is not an external live feed or
independent proof of event lag. A delayed feed can still support honest history
and display, while current forecasts remain unavailable. Source approval must be
reviewed into live_source_policy.json with evidence before enabling a collector.
No amount of extra client caching proves a timing or reuse gate.
