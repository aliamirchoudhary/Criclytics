# Context availability workflow (T037)

This extends the T021/T022/T023 ledgers, not the trained contextual candidate.
No weather, crowd, incident, captaincy or mental-state coefficient is enabled.
Available evidence and a useful predictive feature are different claims.

ContextLedger now accepts weather_observation, captaincy and crowd_event alongside
existing pitch, venue affiliation and fielding annotations. New kinds require a
reuse basis/reference, source/observer, revision, public/private owner scope and
published/observed/effective times. Weather has bounded numeric measurements,
stable venue, expiry and at least one measured value. Captaincy requires explicit
team/player and confirmed-change true/false. Crowd observations identify a prior
canonical delivery attempt and observed/unknown occurrence. No pressure score,
politics label or free-text tactical field is accepted in these numeric records.

Use own observations or a verified permitted source, not unrestricted scraping.
Prepare a private JSON array of1..64records (maximum1MiB), retaining the schema in
MATCH_CONTEXT.md/ANNOTATIONS.md. New weather example value:

```json
{"venue_id":"venue:your-source:id","valid_until":"2026-10-29T12:00:00Z","temperature_c":40,"rain_mm_hour":0}
```

The surrounding record must supply schema_version1, record_id, revision,
match_id, kind, source, observer, published_at, observed_at, effective_at, scope,
rights_basis (own_observation/permitted_extract/licensed), rights_reference and
value. Private records additionally require immutable owner_id. Source identifiers
and references must not contain credentials. This example is a schema, not real
weather or a match observation.

```powershell
python -m criclytics_app.integrations.context_import --file build/observations.json --ledger build/context.sqlite3
```

The importer validates first and applies all revisions in one locked SQLite
transaction. A conflicting revision rolls back the batch. Reimport is idempotent;
corrections are higher immutable revisions. The platform records actual local
ingested_at separately; imported source timestamps never prove earlier platform
availability. This CLI performs no network requests or logging of payloads.

Configure CONTEXT_LEDGER privately to inspect the local read-only endpoint
/api/v1/context-evidence with match_id, before_event_id, optional as_of, venue_id
and team_id. Both socket/Host must be loopback and request same-origin. No owner
parameter, writes, notes or file path inputs. Only public-scope records are
returned, even locally. require_ingested=True prevents imported backfill from
appearing before the platform received it. The API is excluded from caches and
does not create or migrate a ledger during reads. Public callers get unknown
families without personal data. No HTTP authentication is inferred from this gate.

Family summaries retain attribution/revisions. No eligible record means unknown;
different eligible values remain conflict, not an arbitrary winner. Expired weather
is unknown. Current/future attempt crowd/fielding events are excluded. Fielding
uses the existing reviewed/disputed observation grouping. Distinct crowd events
are listed, never collapsed into a global emotional state. No fixed rule converts
rain into lower bounce: surface, covers, moisture and other conditions matter.

What-if assumptions remain in the existing private preparation workspace, linked
from the scenario explorer. They stay in page memory unless explicitly exported;
exported files are readable by anyone holding them. Notes are never sent to the
model/API, persisted automatically or converted to features. Changing assumptions
does not alter probability. Real eligible observations, inter-rater review and
preregistered ablation are still absent; no efficacy claim follows from tooling.

Tests use authored fiction for conflicting weather, expiry, current-attempt crowd
exclusion, batch rollback, ingestion-time leakage and private/remote access. Real
production observations and source rights remain a collection/review dependency.
Rollback: unset CONTEXT_LEDGER; preserve the ledger and private preparation files.
