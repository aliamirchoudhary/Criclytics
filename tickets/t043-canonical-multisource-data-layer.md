# T043: Canonical multi-source medallion contracts

- Status: Planned
- Depends on: T041,T017
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Unify bronze source/run schemas and silver match/person/team/venue/competition/event revisions; exact identity bridge and unresolved queue; gold marts lineage, privacy and schema versions. Measure SQLite versus Parquet/DuckDB before adding dependencies.

## Acceptance and verification

Cross-source identity collisions, revised deliveries, units/timezones, tombstones and withheld data; deterministic rebuild with all rows accounted; old contracts migrated together.

## Limits and handoff

No wholesale replacement of existing data or forced paid lakehouse.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
