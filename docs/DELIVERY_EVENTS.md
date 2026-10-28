# Canonical delivery and replay contract v1

`python -m criclytics_app.pipeline.events --raw-dir <local-raw> --dataset <validated-dataset> --output <fresh-private-sqlite> --limit 100`

This bounded importer defaults to100 historical maleT20I matches (hard maximum500),
verifies selected source-file hashes and never fetches providers. File-order subset
selection is deterministic, not a chronological train/test split. Existing stores
cannot be overwritten. Source data and default serving artifacts remain intact.

SQLite keeps normalized immutable source observations keyed by content hash,
receipts with source-observed time (unknown when absent) and separate local
import/ingestion time. Original raw files remain archived with exact byte hashes;
the normalized observation hash represents parsed JSON content. Metadata binds to
the source dataset, canonical match/participant IDs and recorded innings identity.
Source names are retained only as labels, not the player primary key.

Delivery attempts have stable per-innings attempt numbers and event IDs. Wides
and no-balls consume an attempt but no legal ball; the reducer emits a legal-ball
identity that can repeat across illegal attempts. Revision numbers are explicit;
identical duplicate revisions are idempotent and conflicting same-version payloads
fail. Event-order indexes and latest-revision selection make reordered ingestion
deterministic. Older observations/revisions are retained, including tombstones.
A correction invalidates all later derived state and requires replay, not a silent
mutation of previous observations. Structural insertion/deletion requires explicit
stable source-attempt reconciliation (T026), never ball-label guessing.

`EventStore.events(match_id, as_of=<timezone-aware-ISO>, allow_unknown=False)`
selects the latest revision actually observed by the cutoff and omits unknown-time
history. The retrospective default allows unknown timestamps and latest truth;
it must not be represented as prospective point-in-time evidence. Exact historical
event/publication/observation timestamps remain null. Date fields and local import
times are not substituted for actual delivery availability.

The reducer conserves batting/extras/total, increments official dismissals and
legal balls independently, retains innings/super-over boundaries and partnership
runs, and uses actual source striker/non-striker/bowler IDs before every attempt.
Odd completed runs and known official over ends swap inferred ends. Automatic
wide/no-ball/penalty runs do not imply crossing. After any wicket/retirement,
replacement/crossing position is unknown until a later source observation; the
reducer returns null ends rather than inventing a striker. Source miscounted-over
limits are explicit. Completed innings pre/post penalties are separate controls.

Regular limited-overs chase targets may be derived from the completed prior
innings, but are marked **unverified**. Recorded retrospective target fields do
not establish when a rain/DLS revision was known. `target_revision` controls need
an explicit before-attempt order and observed availability to establish a verified
target. No DLS calculator or pitch/rain inference is fabricated. Tests and super
over targets remain unavailable unless explicitly observed; no two-innings chase
assumption is applied to Tests. Empty/forfeited innings retain explicit metadata.
Target/innings changes are versioned controls or require explicit reconciliation
if match metadata itself changes. Future feature builders must honor missingness.

Golden tests reconcile allfive fictional fixtures with corrected scorer totals,
including illegal balls, penalties, multiple dismissals/retirement and super overs.
They cover duplicate/reordered input, immutable conflicts, corrections/tombstones,
odd-run strike, explicit revised target and as-of revision exclusion. A real100match
sample reconciles23,104 attempts against the corrected innings scorer with zero
provider requests. See audit/delivery-replay-2026-10-28.json for exact counts/size.
This is a bounded historical sample, not live parity or whole-corpus acceptance.
No public event ingest or private-note logging was added. Keep stores outside
public static/dist; selection/backup is local and no raw SQLite files enter Git.
