# Local diagnostics and operating budgets

`GET /api/health` is process liveness, independent of datasets/providers.
`GET /api/ready` and the compatible `/api/status` URL return200 only when all13
required processed JSON artifacts have valid object roots (player index and
completed matches must be nonempty; the latter requires a nonempty data array).
T015 golden subset review established that auxiliary venue bowling tables can
legitimately be empty when no qualifying bowling observations exist. Missing or malformed replacements return503,
even if the repository retains last-good serving data. These are structural
readiness checks, not statistical validation or full artifact hash verification.
Promotion/hash checks belong to T015. Optional live-feed absence/degradation never
fails historical-data readiness. Snapshot age is cache age, not provider event lag.
Dataset schema is null when unknown; model availability/version remain false/null.
The old key-presence and directory listing diagnostics have been removed.

Each API response has a server-generated request ID. JSON log messages contain
only endpoint name, method, status, elapsed time, size and request ID. They omit
raw paths/queries, body, credentials, headers, provider URLs and private notes.
Keep reverse-proxy/Gunicorn access logs disabled or configure them to exclude
query strings too; application redaction does not sanitize upstream access logs.
Counters use a fixed allowlist, per process, reset on restart. A256-entry deque
bounds latency samples. No public metrics dump, paid APM or hosted database is
required. Cache hits, stale fallback, parse errors, provider timeouts/rejections,
quota stops and refresh backoff have separate event names. Quota stops record
provider429/explicit limit failures; they do not prove a daily budget reservation
(which remains T025).

Run `python -m tools.diagnostics --processed-dir <candidate> --samples 20 --output <local-json>`.
The command disables live/Redis and uses a temporary empty cache. Samples are
bounded1?50. Exit0 requires readiness and all sample responses200; otherwise exit1.
The report contains no credentials or raw file paths. It is local operator output,
not a public API. Process memory is reported where the platform supports it.

The2026-10-28 Windows run on schema2.0.1 accepted20/20 bounded list responses:
11,549 bytes each, p50 about108ms, p95 about304ms, max451ms, resident413MB after
readiness loaded required artifacts. No provider requests were made. See
`audit/diagnostics-2026-10-28.json`. This is a single-process local disk/OS-cache
sample, not a hosted capacity guarantee or full load benchmark. Keep one worker,
two threads,32 repository entries,128 cache files,64KiB request bodies and list
limits20/default500/max. Treat512MiB as a local investigation threshold, not a
claim that any host supplies/satisfies it. Measure startup/peak RSS on the actual
existing free host before release; do not add workers, paid memory or Redis to
hide a budget failure. Reduce retained data/indexes if measured limits are exceeded.

For503, inspect fixed artifact states, restore the last verified version using
T015 workflow, then retry. If optional feed is stale, retain historical/replay mode;
check local timeout/quota/backoff counters rather than repeatedly calling upstream.
Use request IDs to correlate redacted application errors. Never attach credentials,
full provider exceptions or private notes to a bug report. No production host or
credential changes were performed for this ticket.
