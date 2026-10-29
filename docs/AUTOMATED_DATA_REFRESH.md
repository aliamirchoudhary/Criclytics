# T041 automated historical refresh

Master plan and its review were committed as386ce44 before implementation.
Use the same job locally or from a scheduler:

```powershell
python -m criclytics_app.pipeline.refresh --store build/automated-refresh-v1
```

No new credential, API subscription, Redis instance or card is needed. This uses
the documented Cricsheet JSON archives for men's Tests/ODIs/T20Is, licensed under
ODC-BY1.0 with attribution. The source register is checked, robots is honored,
URLs are fixed allowlisted official download paths, redirects are rejected and
429/other failures stop without retrying or changing providers. A local successful
job is due again after23hours; GitHub schedules at06:17UTC once per day.

The job store must be separate from public files, application source and original
raw/processed/static data. A marker prevents reuse of unrelated nonempty folders.
Source ZIPs are immutable content-addressed bronze; members have bounded names,
counts, compressed/expanded sizes, JSON schemas and declared populations. Path
traversal, symlinks, duplicate/encrypted/unknown members are rejected. Extraction
uses a fresh snapshot, never a merge with old files. Local originals are unchanged.

ETag/Last-Modified conditional requests reuse hash-verified archived bytes. A304
does not change original received_at. Corrupt local bytes trigger an unconditional
fetch and retain corrupt originals in quarantine when a verified repair arrives.
Per-source metadata advances only after full source validation; it can be reused
after a later build fails. Source check/receipt times are separate from match
dates. HTTP ZIP Last-Modified does not establish per-match historical publication.

The full combined snapshot is scored/rebuilt with the existing corrected schema
and artifact validator. Every input is accounted for, all three formats required,
zero rejected files required; more than20%coverage loss against the previous job
requires review. Per-file hashes identify added/revised/withdrawn matches. Removed
matches cannot be restored from retained older archives. Gold version identity
also includes transformation/source-registry hashes. Unchanged inputs/code reuse
the validated previous candidate. No source-only run replaces a full checkpoint.

State layout, all private/ignored:

```text
store/
  bronze/<sha256>.zip            original archives
  sources/<archive>.json        independently validated fetch metadata
  candidates/<run-id>/gold/     complete immutable corrected dataset + manifest
  runs/<run-id>.json            source clocks, hashes, changes and candidate ID
  latest.json                  latest successful combined candidate checkpoint
  latest-source.json           optional source-only verification checkpoint
  jobs.sqlite3                 cross-process lease
  quarantine/                  retained corrupt local archives, if any
```

A30minute lease excludes overlapping local processes; work cannot publish after
25minutes. Workflow has a25minute timeout and one concurrency group. A4GiB private
store ceiling fails closed; automatic deletion is deferred to the reviewed T042
retention/restore design. Completed candidates and prior original artifacts are
never overwritten. Errors emit only exception TYPE, not provider URLs/payloads.
Existing legacy Unicode progress is captured so Windows consoles cannot abort a
successful computation. Failure leaves the previous checkpoint selected.

.github/workflows/refresh_cricket_data.yml is scheduled/read-only and restricted
to public repository standard runners on main. It uses pinned actions, locked
dependencies and no tokens beyond read checkout. It never commits, pushes,
uploads artifacts, deploys or trains/promotes a model. Source/raw data never enters
static output. The local workflow definition is NOT yet remotely activated.
Schedules run from the default branch and can delay/disable after inactivity;
they are not a live-scoring service or always-on guarantee.

This ticket automates source-to-validated-candidate work. **It does not yet update
the running website automatically.** T042 must provide a verified $0 durable
artifact channel, combined identity/player stores, publication/rollback and job
health after approved integration. Ephemeral runner disks/Actions caches are not
a durable warehouse; no upload/storage bill is enabled here. Automatic data refresh
also does not promote a retrained model. T048 owns fresh frozen ML evaluation.

Verification covers authoritative removal, conditional reuse, corrupt repair,
invalid refresh preserving last good, unsafe archives/expansion,429stop and a
competing worker lease. Real source/candidate evidence is recorded separately in
docs/audit/automated-refresh-t041-2026-10-29.json after the actual build succeeds.
Current UI/data/model selection remains unchanged for the owner's review.
