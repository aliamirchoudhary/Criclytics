# Public read serving and measured limits

Historical public statistics use a per-worker response LRU:128entries,8MiB total,
512KiB per response and30second TTL. Identical cold reads share one computation.
At most32distinct computations are tracked; followers wait at most2seconds before
retryable503. Errors/oversized responses are not retained. Queries are bounded
to4KiB/20fields with bounded names. Existing JSON repository reuse remains below.

Only explicitly allowlisted historical routes participate. Authorization/cookie
requests, live collectors/scores, workspaces, scenarios and private scouting are
excluded. CORS/request IDs are fresh per request. ETag/If-None-Match works for
public JSON; validation runs before lookup. Static files already use conditional
responses. No new external service, Redis restoration, API key or card required.

Selected dataset directories are immutable: restart on promotion. Do not mutate
a selected production directory in place. TTL also bounds old responses. Factory
configuration PUBLIC_READ_CACHE_ENABLED=False disables this layer; tests disable
it by default. Diagnostics contain counts/limits only, never keys or notes.

Local Windows CPU,100concurrent HTTP clients, two application slots, four APIs:

| Batch | Failures | Requests/second | p50 | p95 |
|---|---:|---:|---:|---:|
| 100 cold requests | 0 | 34.12 | 1,754ms | 2,611ms |
| 100 warm requests | 0 | 117.54 | 325ms | 445ms |

Four responses computed;196requests hit cached data; three waited behind initial
computation. Zero provider requests. Cache437,195bytes; process working set83MB
to115MB. Includes local HTTP/client overhead and cached files. This does not
certify Gunicorn, Cloudflare, a sleeping free host, geographic latency or uptime.
Evidence: [capacity report](audit/public-capacity-t035-2026-10-29.json).

Reproduce with python -m tools.measure_public_capacity and --processed-dir,
--identity-registry, --player-store, --output local artifact arguments. The tool
binds127.0.0.1 on an ephemeral port, never a hosted load-test URL. Production
remains one worker/two threads. Each worker has its own LRU; external quota/refresh
coordination remains SQLite. Reads never add a provider strategy. A future timely
feed must publish one immutable forecast per state independently of visitor count.
Free-host memory/persistence/sleep/request limits still constrain capacity.
Hosted observations and capacity trials belong to reviewed release work.
