# T038: Timely authorized next-delivery source

- Status: Blocked; no approved $0 timely/reusable source
- Branch: chore/t038-live-source-gate
- Base: f4c23d2
- Depends on: T025,T026,T034
- Budget: $0; no card or metered fallback

Verify reuse rights, free/no-card/no-overage limits, actual delivery lag/corrections and actor confirmation before enabling an external collector. One shared producer; no per-visitor polling or widget DOM extraction. Retain manual/replay modes.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Primary pricing/widget terms rechecked2026-10-29. CricketData100/day and stated
minutes delay cannot support next-delivery timing; a4hour30second trial needs480
calls. Widget display does not grant feed ingestion/ML reuse. No approved source
exists for actual lag/correction trial, so benchmark remains null. Replay/manual
and isolated display retained; network allowlist empty. LIVE_SOURCE_ACCEPTANCE.md
records evidence, safe trial steps and exact approval gates. No scraping bypass,
provider request, token use, paid fallback, deployment or fabricated latency.
Continue independent T039; source approval/prospective trial require external evidence.
