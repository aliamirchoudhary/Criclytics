# Source-cutoff state reconciliation

Reconciler reads the permitted collector's last confirmed source cutoff using
read-only SQLite. It reconstructs canonical latest-known revisions at that cutoff,
then uses the same reducer/LocalHistory/vector as offline features. Source IDs are
preserved; no fuzzy provider/history join or new external collector is introduced.
Unknown precise event time means event lag=null, separate from known capture age.
Manual/replay never becomes a claimed verified live feed.

A16entry cache keys by durable source receipt/revision counter and eligible context,
not wall-clock query time or SQLite WAL-file churn. Writers must use the collector;
raw workspace files are not an out-of-band editing API. Repeated readers add no
collection or replay work. All pending reservations block forecasting, and a late
reserved correction increments the source revision counter even if a newer capture
already published. A mismatched old score confirmation then abstains until renewed.
Expired workers check lease ownership before/after commit; recovery is idempotent.
Repeated physical events in distinct observations preserve first canonical
provenance while retaining every raw observation. Semantic same-revision conflicts
still fail. No original observation or canonical revision is overwritten.

Missing logical attempts block inference; explicitly tombstoned attempts remain
in the sequence audit while legal/actual attempt counts replay without them.
Announced next actors/attempt and expected runs/wickets/legal balls must agree.
The next attempt must be explicitly confirmed open; its announcement expires after
15seconds, source capture after60seconds. Stale, killed, quota-blocked, pending,
paused, completed, abandoned, missing or contradictory data has an explicit reason.
Unknown/missing optional context stays missing rather than becoming a false fact.
Source-announced ends take precedence over uncertain inferred crossing/replacement.

Innings end controls declare final score/wickets/legal balls; contradiction or
an unconfirmed prior innings blocks a following innings forecast. Rain target and
scheduled-ball revisions are observed controls with explicit effective attempt
order; future-attempt controls are not applied early. Reaching target/ball limits
or a complete innings blocks further forecasts there. Test and super-over targets
are never guessed. Extra innings can be appended only through an explicit2+metadata
revision; prior match/innings identities/rules remain immutable. Original metadata,
source observations and as-of earlier views persist. Other metadata changes need
review, not silent reinterpretation. No DLS formula is fabricated.

Online annotation selection also requires actual local ingestion by cutoff;
trusted imported source-time claims alone are insufficient. Unknown legacy
ingestion times are omitted from online contexts. Eligible annotations are still
not model inputs; public derived views omit private-owner records. Displayed
annotation details are bounded100 groups while provenance remains in the ledger.

StateLedger retains immutable derived-state hashes/snapshots and separate
invalidation rows. Stale/blocked/current-state changes do not edit old snapshots.
Source cutoff/revision ordering prevents an older reader regressing the current
pointer. Issued forecasts are append-only, deduplicated by state/model; a corrected
forecast for the same target references the previous ID. An older state cannot
issue a new forecast after being superseded; issue time/target must match recorded
state. No model service is enabled by this ticket; fixture forecasts test ledger
immutability only. Limits cap snapshots/forecasts per match and global store, with
explicit exhaustion rather than automatic data deletion.

80unit tests (79pass/one optional skip) include correction/reorder/gap/tombstone,
reconnect/abandonment, target/schedule, appended metadata/as-of, old-reservation,
first-seen provenance, immutable forecast replacement and shared-vector cases.
`python -m tools.check_stream_parity` replays Cricsheet historical match1001349:
250before-attempt vectors agree, final totals reconcile and100repeat readers cause
zero rebuilds. Virtual arrival time, zero external calls; this is recorded historical
replay emulation, not actual provider/human latency or prospective availability.
See audit/stream-parity-2026-10-28.json. No public write route/default dataset or
production resource changes accompany this ticket.
