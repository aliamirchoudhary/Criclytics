# Attributed fielding and incident observations

Local ContextLedger accepts fielding/incident records tied to canonical delivery
attempt IDs, with source/observer, published/observed/effective time, optional event
time, confidence, review state/reviewer, revision and public/private owner scope.
Confidence is observed/uncertain/disputed observation quality, not a probability
or evidence of a player's mental state. No incident or missed catch is inferred
from historical score changes. Source rights must cover any imported observation.

Missing coverage means unknown. Explicit reviewed occurred=false is a recorded
negative observation, different from no annotation. Unknown actors stay null.
Records group by attempt/type/chance ID, so an unknown versus identified fielder
does not double count the same chance. Multiple distinct chances require explicit
source chance identifiers; actor disagreements remain visible. Counts describe
only confirmed reviewed observations, never a complete fielding success rate.

Backfilled records become eligible only after max(publication, observation,
effectiveness); they cannot enter earlier forecasts. A target attempt's own
annotation is excluded even if timestamps are wrong. Earlier attempts/innings may
be consumed deterministically; unsupported attempt identity fails. Latest known
revisions are selected as of cutoff, conflicting observers remain uncertain and
prior versions persist. A reviewed claim may take precedence over an unreviewed
claim, but conflicts between reviewed sources never silently pick a winner.

Tactical/private notes are a separate T029 workflow: annotation payloads use an
exact field allowlist, without free-text plans. Private records require immutable
owner IDs and are omitted from other/public local views. This local helper is not
HTTP authentication; never trust a caller-supplied owner identity in a future API.
Future live ingestion must assign its own observed/recorded timestamp rather than
allow public backdating. Raw/private contents are not logged or served as assets.

Tests cover missing/false/current-target distinction, delayed backfill, conflicting
sources, corrected revisions, ownership filtering, note separation and actor
uncertainty without duplicate counts. `python -m tools.check_annotations` replays
three authored fictional records in reverse/duplicate order, retaining one
conflicting catch assessment and one explicit misfield. The fixture's review
states are assertions by the fixture author, not a real coach reviewing a match.
See audit/annotations-2026-10-28.json. Real reviewed fielding observations, rights
clearance and predictive ablation remain unavailable; no model feature is enabled
or benefit invented. The replay pipeline works with no annotations at all.

The ledger also records local ingested_at separately. Older local rows migrate
with unknown ingestion time, never a fabricated historical value. Imported
source-observed timestamps are claims requiring provenance; they are not proof
the platform had the record then. Future live/manual ingress must own capture
time. The current module exposes no public ingest surface.
