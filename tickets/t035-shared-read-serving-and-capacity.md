# T035: Shared read serving and capacity

- Status: Implemented locally; hosted verification pending
- Branch: feat/t035-shared-read-capacity
- Base: 0e40637
- Depends on: T033
- Budget: $0; no card or metered fallback

Bound and coalesce identical public reads; separate them from collection; add conditional immutable/static-friendly responses where safe; measure actual cold/warm local HTTP concurrency, memory and provider calls. Preserve private/no-store workspace and coach boundaries.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Implemented bounded public historical response LRU, identical-request coalescing,
conditional ETags, query size/count/name limits, retryable busy responses and
counts-only diagnostics. Private/scenario/replay/live requests excluded. No
provider or Redis dependency. See docs/PUBLIC_READ_CAPACITY.md.

Actual local HTTP100cold+100warm requests at100client concurrency/two application
slots: zero failures/provider calls; four computations; warm p95~445ms.
Evidence: docs/audit/public-capacity-t035-2026-10-29.json.96tests95pass/one skip,
including concurrency, expiry/eviction/size/busy, fresh CORS/request IDs,304,
query rejection and private exclusions. Compilation passes. T034 full browser
matrix also passed95cases/four interactions; report retained in docs/audit/.
No hosted stress test, remote operation, deployment or billing activation.
