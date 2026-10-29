# Master plan double-check before implementation

Reviewed2026-10-29 against the complete owner prompt, source terms and current code.

| Check | Finding / decision |
|---|---|
| Every audience covered | Fan/history/coach/selector/broadcaster/analyst journeys and sourced query service present |
| More than a score site | ML, preparation, search, rivalry, selection and exports are distinct deliverables |
| Automatic updates | Daily source job, authoritative reconciliation, durable publishing and monitoring separated; no manual monthly copying target |
| Ranking cadence | Corrected monthly assumption using ICC FAQ: weekly players/event-driven teams |
| Scraping feasibility | Allowed adapter in principle; Google /search rejected by robots/terms; direct source trial remains a real task |
| Data beyond ball history | Weather/competition/fielding/crowd/captaincy/media sources, timing and missingness mapped |
| Psychological assumptions | Observable sporting proxies separated from unobserved emotions; no invented labels/coefficients |
| Training/runtime consistency | One feature registry, availability clocks, role/format scope, parity and immutable model/state issue IDs |
| Warehouse/lakehouse size | Logical medallion on files/SQLite; Parquet/DuckDB only when measured; no giant new paid stack |
| Source withdrawals | Full archives authoritative; old retained files never merged to resurrect withdrawn matches |
| Photos | Commons/Wikidata/licensed Flickr/contributed assets with exact IDs, per-file rights, credits,429stop and quality checks |
| $0 compute/storage | Public standard runner guard, no artifact storage assumption, no paid LLM; durable delivery explicitly T042 |
| Thousands of users | Static CDN and dynamic live quota arithmetic separated; no false unlimited Worker/Redis claim |
| Scheduled is not activated | Workflow file on local branch cannot run remotely until approved publication/default-branch integration |
| Data is not model promotion | Automatic collection/rebuild; frozen evaluation before retraining/promotion; previous artifacts unchanged |
| Privacy/security | No public raw/models/notes, controlled sources, bounded archives/requests, read-only scheduled permissions |
| Scope of first implementation | T041 only; source-to-validated candidate and schedule definition. Publishing/UI/other sources retain own tickets |
| Acceptance honesty | Real local download/build evidence required; hosted scheduling/durable application refresh not claimed before T042 |

No unresolved design issue prevents T041. Source/publication and prospective
evidence gaps remain visible in later tickets, rather than hidden as completed.
