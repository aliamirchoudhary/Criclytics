# Budgeted local manual/replay collection

T016 approved only authorized local manual/replay input. LocalCollector does not
import a network client, poll providers, run a browser or expose HTTP write routes.
External source modes fail. Constructor/CLI is disabled unless explicitly enabled;
this creates no cloud service or billing/card requirement. Existing cached provider
files/resources and default serving configuration are untouched.

Create a declaration with `manual_session` (teams explicitly in batting order,
known date/scope; unknown gender/competition stays unknown), then construct attempts
with `manual_delivery` from current replay state and stable announced participant
IDs. The helper supports regular limited-overs sessions; Test/extra innings require
explicit metadata/reconciliation. Match IDs are namespaced match:manual:<id> so
an unsourced manual session cannot overwrite a historical match. No identity join,
team nationality, toss outcome, ball event time or predictive eligibility is guessed.

A local input JSON contains schema_version1, match_id, a bounded unique
observation_id, explicit match status, events (max50) and optional next_context.
Session and input are each bounded64KiB. Next context requires distinct striker,
non-striker and bowler IDs, innings/attempt, not_started_confirmed and explicit
expected runs/wickets/legal balls. No announcement means no next-attempt readiness.
Collector capture/announcement timestamps are assigned by its own UTC clock;
input event time is optional/unknown and cannot be in the future. Unknown event
lag is distinct from the known capture age. Arbitrary tactical/private fields are
not accepted as observation metadata.

`python -m criclytics_app.integrations.collector --store <private-events.sqlite3> --mode manual --session <session.json> --observation <input.json> --enable-local`

Use mode replay for clearly labelled historical/authored fixtures. Receipts print
only status/IDs/capture time/cost, never input bodies or notes. Accepted/duplicate
returns exit0; disabled/deferred/budget-stopped returns2. kill/resume commands need
only store/mode: `--kill` stops all workers, `--resume` clears that switch without
approving any external source. Kill switches are never silently reset at startup.

A separate same-volume coordinator SQLite store serializes one30second owner per
match, expires abandoned leases and retains durable input receipts/cursors.
Conflicting same-ID content fails. Duplicate accepted inputs do not consume quota;
retries retain first capture time but reserve another processing attempt, never
a falsely fresh timestamp or a quota bypass.
Malformed processing fails atomically in EventStore, retains last-good state and
adds5second backoff. Raw source observations/events/revisions remain immutable.
Source mode changes/clock regression stop; unknown sessions do not fabricate state.

Shared processing ceilings default60batches/minute and5000/day across all sessions,
not per visitor/worker. Limits persist and another worker cannot raise them merely
by supplying higher constructor values; lower limits can reduce the shared budget.
Reservation happens before processing; failures can consume a reservation (safe
conservative accounting), never trigger paid fallback. At most128sessions are
admitted. Operational counters retain7days; raw observations are never purged.
Concurrent accepted/duplicate workers preserve one observation; an abandoned
reservation plus a retry can conservatively charge two attempts. This coordinates
one shared local volume, not independent hosts or an always-on cloud SLA.

Public readers must use read_snapshot, a read-only connection.100sample readers
add zero collection work. Snapshot exposes manual/replay mode, capture age, killed
and stale state (default60seconds), source status and announced context.
Failed/pending ingest, active owner/backoff, exhausted shared budgets and kill
state also mark source_health/blocked immediately; last-good display data is not
a guarantee the next forecast can be issued. Sleeping/
restarted collectors become stale; no keepalive trick or fake live flag is used.
A bounded batch can finish if a kill arrives during its atomic commit; no new
batch begins after the switch is seen. Cross-database receipt/data publication is
recoverable by idempotent retry, not represented as an atomic multi-file transaction.

Fake-clock quota/lease/kill/failure/capture tests, parallel workers and persisted
limit/reader checks pass. `python -m tools.check_collector` is an agent-run authored
replay sample with real local processing timing and0external calls/dollars/card.
It is not a human-scoring latency/accuracy or live-provider benchmark. See
 audit/local-collector-2026-10-28.json. Actual operator/human field use is pending.
Keep stores/private session files under ignored build/ or data/events/, outside
public assets. Restore observations/cursors together on the same volume. Do not
start an unattended hosted worker or activate a paid resource for this adapter.
