# T015: Version datasets source rights and reproducible builds

- Status: Planned
- Priority: P1
- Depends on: T009,T010
- Branch: fix/t015-version-datasets-source-rights-and-reproducible-builds
- Base: latest dev

## Problem

Raw/processed coverage differs without an exclusion ledger; schema/build provenance and reliable artifact restore are missing.

## Scope

Create source registry with licensing/attribution/redistribution/update constraints and separate metadata terms. Hash/version corpus subsets and outputs with parser/schema/build versions, date/format/gender coverage and rejected-file reasons. Define free/local artifact restore/retention without raw Git commits.

## Acceptance criteria

- [ ] Bounded rebuild reproduces manifest and accounts for every excluded raw file
- [ ] Source rights and attribution are documented per data family
- [ ] Promotion validates artifact hashes/schema and retains last-good snapshot
- [ ] UI/evaluators receive accurate coverage and data cutoff

## Validation

Clean subset rebuild, corrupted/missing artifact tests, provenance/licence review and documented restore drill.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
