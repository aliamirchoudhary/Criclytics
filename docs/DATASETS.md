# Dataset identity, rights and restore

The machine-readable registry is `criclytics_app/pipeline/source_registry.json`
(reviewed2026-10-28). JSON match data and the separate People/Venue Registers
are attributed Cricsheet inputs underODC-BY1.0. Derived aggregates identify their
changes and retain source/license links. XML is a different licence and is not
an input here. Provider identifiers do not license provider scorecards or images.

Primary sources: [Cricsheet licensing](https://cricsheet.org/licensing/),
[register metadata and licence](https://cricsheet.org/register/) and
[ODC-BY1.0](https://opendatacommons.org/licenses/by/1-0/).
[ICC website terms](https://www.icc-cricket.com/about/the-icc/legal-notices/website-terms-of-use)
reserve content rights and restrict commercial use without a licence. Legacy
rankings/images are not cleared for general public redistribution. CricAPI and
RapidAPI account-specific rights/limits remain unverified. Their caches, curated
biographies and pitch narratives are not part of verified dataset promotion.
T041 adds bounded official Cricsheet archive refresh; unapproved live collectors remain disabled. Attribution is not a substitute for missing
rights; separate brand/image/personality rights must be checked independently.

## Rebuild and verify

`python -m criclytics_app.pipeline.rebuild --raw-dir <local-corpus> --output <fresh-candidate> --limit 20`

Omit limit only for an intentional full rebuild. The candidate is fresh and
outside raw data. Every raw JSON filename is counted: selected inputs have
SHA256s; rejected selected files retain codes in difference_report.json;
unselected and unsupported-directory files have explicit reasons in manifest.json.
Subset exclusions are inventory records, not claims that excluded bytes were
hashed. Selected source bytes and output/code hashes define the reproducible
subset identity. Normalizations remain in-memory and audited. Originals stay intact.

Manifest version1 and schema2.0.1 include deterministic dataset_id (canonical
manifest hash), source-registry hash, parser code hashes and output hashes.
coverage.json reports observed format/gender/count/date coverage, source licence
and attribution. The cutoff is the latest observed match date, **not** proof of
when any statistic was publicly knowable. Publication/observation times remain
null when unknown; before-delivery feature work must enforce its own as-of rules.

`python -m criclytics_app.pipeline.artifacts validate --candidate <candidate> --expected-manifest-sha256 <trusted-sha256>`

Validation checks supported versions/identity, an exact JSON artifact allowlist,
hashes, object roots, core player/match nonemptiness and coverage/accounting totals.
Auxiliary tables can be empty on small subsets with no qualifying observations.
It rejects escaped paths/symlinks and malformed/missing/corrupt artifacts. Preserve
an expected manifest digest separately from the dataset (operator release record
or offline backup); a self-hash is integrity metadata, not a digital signature or
proof that an untrusted download is authentic. No pickle/model loading is involved.

## Local promotion and restore

`python -m criclytics_app.pipeline.artifacts promote --candidate <candidate> --store <private-store> --expected-manifest-sha256 <trusted-sha256>`

Use ignored build/ or data/datasets/, never static/dist output. Promotion copies
only verified JSON artifacts and manifest, validates the copy, then atomically
replaces current.json. A SQLite transaction serializes promotions on that volume;
the atomic pointer is authoritative if interruption prevents audit-ledger commit.
Partial staging is never selected. Immutable versions and prior selected ID are
retained; there is no automatic deletion or paid storage. Failed candidates leave
the old pointer and data untouched. No remote service is required.

Set DATASET_STORE to that private store and restart Flask to select it. Startup
validates the selected version once and pins PROCESSED_DIR for that process;
workers pin one verified version. Empty DATASET_STORE leaves data unselected
unless PROCESSED_DIR is explicitly configured or LEGACY_DATA_ENABLED=1 explicitly
opts into the original archive. Root-file fallbacks have been removed. `/api/coverage`, readiness and the UI expose coverage/identity,
not filesystem/source-input lists. Legacy datasets return unknown metadata.

Restore by promoting a retained `store/versions/<old-id>` with its trusted digest,
then restarting. Keep at least the current and previous validated version plus
an independent local/offline copy where available. Retention is constrained by
actual disk capacity; review old versions explicitly rather than auto-deleting.
No raw data/model artifacts go in Git, public assets or an indiscriminate upload.
An ephemeral free host is not a durable backup. Production promotion and hosted
restore remain release/operator acceptance, not implied by this local drill.

Golden tests rebuild twice with identical manifests, account for subset/unknown
folder exclusions, promote two versions, restore the first, and reject corrupted,
missing and escaping artifacts without changing the active pointer. The full
local corpus evidence is recorded separately in audit/dataset-manifest-2026-10-28.json.
