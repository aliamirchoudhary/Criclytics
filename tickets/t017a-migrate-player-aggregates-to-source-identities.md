# T017A: Migrate historical player aggregates to source identities

- Status: Planned
- Priority: P1
- Depends on: T010,T015,T017,T018
- Branch: work/t017a-identity-aggregates
- Base: previous local ticket branch, per session override

## Problem

T017 found68colliding raw roster labels and multiple aliases. Existing name-keyed
summary tables can combine different people or split one identity. Ambiguity
containment/coverage warnings do not constitute a corrected aggregate migration.

## Scope

Build a separate non-overwriting source-ID player aggregate candidate using the
validated scorer/identity mapping. Preserve original artifacts, names/aliases,
team-membership uncertainty and source hashes. Expose correct source-ID profiles
and safe name resolution without silently combining legacy summary rows.

## Acceptance criteria

- [ ] Same-name people remain separate and aliases of one source ID aggregate once
- [ ] Player/year/opponent/venue/record totals reconcile to canonical scored innings
- [ ] Nationality is not inferred from first observed team; actual membership is explicit
- [ ] Version/hash/dataset-bound opt-in preserves old artifacts and compatible name URLs

## Validation

Portable collision/alias/two-innings fixtures, full bounded-memory source rebuild,
original artifact checks, API name/ID ambiguity/coverage and source-stat reconciliation.

## Handoff

This is a required child of the T017 discovery, not an untracked statistical caveat.
Read audit/architecture/workflow and preserve the $0/no-card/source-rights rules.
Complete before claiming coach scouting summaries are identity-correct. No automatic
production promotion. Record evidence in this ticket and SESSION_PROGRESS.md.
