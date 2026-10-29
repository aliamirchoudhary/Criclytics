# T035: Shared read serving and capacity

- Status: Planned
- Depends on: T033
- Budget: $0; no card or metered fallback

Bound and coalesce identical public reads; separate them from collection; add conditional immutable/static-friendly responses where safe; measure actual cold/warm local HTTP concurrency, memory and provider calls. Preserve private/no-store workspace and coach boundaries.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.
