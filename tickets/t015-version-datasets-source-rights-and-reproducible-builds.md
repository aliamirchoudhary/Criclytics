# T015: Version datasets source rights and reproducible builds

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T009,T010
- Branch: work/t015-dataset-manifests
- Base: T014 8d61bda

## Problem

Raw/processed coverage differs without an exclusion ledger; schema/build provenance and reliable artifact restore are missing.

## Scope

Create source registry with licensing/attribution/redistribution/update constraints and separate metadata terms. Hash/version corpus subsets and outputs with parser/schema/build versions, date/format/gender coverage and rejected-file reasons. Define free/local artifact restore/retention without raw Git commits.

## Acceptance criteria

- [x] Bounded rebuild reproduces manifest and accounts for every excluded raw file
- [x] Source rights and attribution are documented per data family
- [x] Promotion validates artifact hashes/schema and retains last-good snapshot
- [x] UI/evaluators receive accurate coverage and data cutoff

## Validation

Clean subset rebuild, corrupted/missing artifact tests, provenance/licence review and documented restore drill.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented locally; review/integration pending. Manifest version1 adds deterministic identity, output/source/code hashes, complete selected/rejected/excluded inventory and observed coverage. Public coverage has no filesystem paths or invented publication times. Promotion validates exact JSON allowlist, schemas/roots/hashes and retains current/previous immutable versions; DATASET_STORE is opt-in at startup. Source rights reviewed with primary links; legacy provider/ranking/reference permissions remain uncleared. Small golden subsets legitimately have empty auxiliary venue-bowling tables, so validation/readiness require nonempty core player/match data while allowing valid empty auxiliary object roots. Roll back by reselecting a retained verified version and restarting; never overwrite original processed/raw data.

### Session update 2026-10-28T12:03:53+00:00

Chained from T014 8d61bda. Primary Cricsheet JSON/register licensing and ODC-BY1.0 reviewed2026-10-28; ICC terms do not establish public redistribution rights and provider terms remain unverified. No collectors enabled.

### Session update 2026-10-28T12:10:23+00:00

Full6,651-input rebuild accepted6,651 with zero rejects/exclusions;15output and all pipeline hashes verified. Dataset e6dce5850e36a851f95537e702fc9f782fe26f0dd98c15448b2a767c0f4c2da3 covers2001-12-19 through2026-04-10 (877Test/2520ODI/3254T20I). Immutable local-store promotion and375/1440 coverage UI checks pass; default serving unchanged.47tests46pass/one optional skip; deterministic subset manifests and two-version restore/corruption tests pass. See DATASETS.md, source_registry.json and audit/dataset-manifest-2026-10-28.json. No production promotion/deployment.
