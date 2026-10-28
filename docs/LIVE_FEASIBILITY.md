# Zero-budget live-source decision ? 2026-10-28

Decision: **NO-GO for automated external live feeds; GO for historical replay
and local manual scoring of matches the scorer is authorized to record.** No new
account, subscription, credit card, billing activation or metered fallback.
No real live endpoint was polled. Existing credentials remain unused/deferred.
This rejects unproven timeliness/rights; it is not a claim that no suitable future
provider can exist. Re-review dated primary terms before changing the gate.

| Candidate | $0/card/quotas | Delivery, latency and correction evidence | Reuse rights and decision |
|---|---|---|---|
| CricketData/CricAPI | Official pricing says no card,100calls/day | Pricing says minutes behind; terms say registered lag30s, conflicting descriptions with no measured SLA. No correction stream established. | Terms restrict personal/non-commercial use and commercial use requires credits. Public platform redistribution not cleared; reject automated feed. |
| RapidAPI Cricket Live Data | Basic250/month; marketplace freemium requires card; listed bandwidth overage | Scorecard features, no established per-delivery revision/latency guarantee | Provider-specific rights not established; reject card/metered plan. Marketplace genuinely FREE APIs differ from freemium, but no qualifying cricket delivery source was verified. |
| OpenCricketAPI Starter | Official5000/month,60/min,no card; no automatic overages | Live summaries offered; delivery/live-centre access belongs to paid Developer tier. Advertised20s refresh is not measurement. | Terms explicitly do not grant redistribution rights for ESPN-sourced data. Reject for public next-delivery feed; historical Cricsheet access is available directly. |
| Cricsheet JSON/register | Public historical downloads; no card/account needed | Completed/history data; no live event timestamps or correction SLA | ODC-BY attribution path verified; GO historical replay. Current download omissions/withheld matches mean local old snapshots are not current source completeness. |
| ICC/Cricbuzz/ESPN pages or browser automation | Public readability proves neither permission nor free service rights | Selector stability, rate limits, event completeness and lag unproven | ICC terms reserve content rights; no written automation/reuse clearance obtained for other pages. NO-GO scraping/undocumented endpoints. No attempts around login, CAPTCHA, robots restrictions or quotas. |
| Authorized local manual scorer | Own local machine; no provider quota/card | Enter actual delivery/observation/revision times. Human speed and correction errors must be measured in a real pilot. | GO only for own permitted observations; not copying a restricted broadcast/feed. Private/replay label until evidence supports freshness. |

Primary sources reviewed:

- [CricketData pricing](https://cricketdata.org/pricing/) and [terms](https://cricketdata.org/terms-of-use/).
- [RapidAPI plan categories](https://docs.rapidapi.com/v2/docs/api-pricing) and [Cricket Live Data pricing](https://rapidapi.com/sportcontentapi/api/cricket-live-data/pricing).
- [OpenCricket pricing](https://opencricketapi.com/pricing) and [terms section7](https://opencricketapi.com/terms).
- [Cricsheet downloads](https://cricsheet.org/downloads/) and [licensing](https://cricsheet.org/licensing/).
- [ICC terms](https://www.icc-cricket.com/about/the-icc/legal-notices/website-terms-of-use).
- [Playwright browser dependencies](https://playwright.dev/python/docs/browsers), [Docker requirements](https://playwright.dev/python/docs/docker), [HF Spaces overview](https://huggingface.co/docs/hub/spaces-overview).

## Bounded experiment and capacity

`python -m tools.live_feasibility` uses36 fictional virtual-time deliveries and
one correction, no real-time waits and zero external API calls. A144s poll example
fits100calls across four hours; a30s schedule alone needs480calls, before discovery,
retries, other matches or detail calls. Full-history snapshots can eventually
recover all event records while still missing timely prediction opportunities.
The report measures simulated lag, late opportunities and correction observation,
not live quality. Actual external lag/missed events/corrections remain null because
no approved live source was available. A2s synthetic manual-input schedule is a
pipeline scenario, not evidence that humans score that quickly.

A local Chrome DOM fixture demonstrates selector breakage after a revision and
records renderer JS heap. Total browser RSS remains unmeasured; heap is not a
memory budget. Chromium plus OS libraries/processes consumes resources beyond the
Flask process, so browser automation cannot be assumed to fit any free worker.
Never put browser polling in each visitor's request. Future approved collection
would need one bounded scheduler, durable cursor, shared quota reservation,
source timestamps/revisions and abstention on sleep/staleness.

The current HF documentation states that creating Docker/Gradio compute Spaces
requires a paid plan, and free hardware can sleep. Preserve the project's existing
Space; its grandfathering/continued entitlement is unverified. Do not create a
replacement paid resource or use keepalive loops to circumvent free-host limits.
Local/manual execution remains usable without a cloud worker. Cloudflare static
assets do not run the Python collector. No always-on or latency guarantee is made.

## Enforced handoff

`integrations/live_source_policy.json` is the dated decision; its network allowlist
is empty. Legacy web refresh and CLI CricAPI/RapidAPI/rankings primitives fail
closed before network requests, even if an old environment flag/key is set.
Cached historical reads remain available with stale/unknown labels; authorization
failures increment a fixed diagnostic counter. Unit tests mock explicit approval
only when exercising lease/error handling, never to call a real provider.

T025 must implement a budgeted **local manual/replay adapter**, not an external
HTTP/browser collector. A future provider needs a separately reviewed evidence
change for zero cost/no card/no overages, redistribution/retention permissions,
real lag/coverage/corrections and sustainable quotas. Do not silently substitute
another source when the approved mode is unavailable. Existing production caches
and credentials have been preserved, not refreshed or deleted.
