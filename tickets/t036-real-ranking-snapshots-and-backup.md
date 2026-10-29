# T036: Real ranking snapshots and backup

- Status: Import/backup implemented locally; public source rights blocked
- Branch: feat/t036-ranking-snapshots
- Base: 054c0a5
- Depends on: T033
- Budget: $0; no card or metered fallback

Implement real-source snapshot import/parser validation, dated provenance and atomic last-good backup. A personal-use source can remain local-only; public redistribution requires an approved basis. No hardcoded current fallback.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Offline strict importer, official date provenance, atomic current/retained SQLite
slots and corrupt-current fallback implemented. Actual ICC T20I batting20rows
and teams100rows dated2026-10-27 verified locally through ordinary Chrome.
Private-only personal-use scope; public API returns unavailable rather than old
hardcoded ratings. UI category buttons/source dates/backup/empty states migrated.
No network collector enabled. See docs/RANKING_SNAPSHOTS.md for source rights,
import instructions, backup limits and release blocker.

98test suite97pass/one skip before an added tie/zero/team-shape test; final focused
three tests pass. Real375/1440rankings flows pass and broader cricket workflows
pass. Python compilation/changed JS syntax pass. Other ranking categories/formats
need actual sources; source rights for automated public redistribution unresolved.
