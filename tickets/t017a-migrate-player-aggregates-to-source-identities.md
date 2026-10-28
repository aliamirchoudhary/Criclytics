# T017A: Migrate historical player aggregates to source identities

- Status: Implemented, awaiting review
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

- [x] Same-name people remain separate and aliases of one source ID aggregate once
- [x] Player/year/opponent/venue/record totals reconcile to canonical scored innings
- [x] Nationality is not inferred from first observed team; actual membership is explicit
- [x] Version/hash/dataset-bound opt-in preserves old artifacts and compatible name URLs

## Validation

Portable collision/alias/two-innings fixtures, full bounded-memory source rebuild,
original artifact checks, API name/ID ambiguity/coverage and source-stat reconciliation.

## Handoff

This is a required child of the T017 discovery, not an untracked statistical caveat.
Read audit/architecture/workflow and preserve the $0/no-card/source-rights rules.
Complete before claiming coach scouting summaries are identity-correct. No automatic
production promotion. Record evidence in this ticket and SESSION_PROGRESS.md.

### Session update 2026-10-28T14:19:17+00:00

Required child from T017 collision discovery, chained from T026 24b42a8. Build separate source-ID SQLite player/profile/year/opposition/venue/record candidate; preserve all original artifacts, no nationality inference or automatic promotion.

### Session update 2026-10-28T17:09:38+00:00

Source-ID SQLite candidate build/player-ids-v1-final: all6,651 raw hashes verified;5,125 rostered/5,050 scored identities;2,764,241 batter runs/129,490 batting innings and99,625 credited wickets/86,051 bowling innings reconcile. All5,125 exported profiles checked against yearly/opposition/venue totals; record rows reconcile. Original artifacts unchanged. Optional dataset/registry/database-bound read-only player/profile/search/compare/ranking/record/venue queries; alias collisions409 with directory recovery, nationalitynull/observed memberships.82tests81pass/one optional skip; compilation/changed JS syntax pass. Chrome375/1440 directory/stable-ID/profile/ambiguous recovery passes without page errors/overflow. Evidence docs/audit/player-id-aggregates-2026-10-28.json; migration docs/PLAYER_ID_AGGREGATES.md. No promotion, push or deployment. Initial development rebuild failed SQL placeholder count; fixed before fresh final rebuild, incomplete candidate retained only under ignored build.
