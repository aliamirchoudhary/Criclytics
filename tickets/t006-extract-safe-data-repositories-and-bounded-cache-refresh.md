# T006: Extract safe data repositories and bounded cache refresh

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T004,T005
- Branch: fix/t006-extract-safe-data-repositories-and-bounded-cache-refresh
- Base: latest dev

## Problem

JSON reparses per request; writes race, Redis age is wrong, locks grow and workers do not share backoff/quotas.

## Scope

Extract legacy data/cache helpers into services with versioned immutable snapshots and indexed detail lookup. Use atomic writes, explicit freshness/stale timestamps, bounded keys/locks, isolated app state and a documented cross-worker refresh strategy that needs no paid Redis.

## Acceptance criteria

- [ ] Unchanged processed files are not reparsed for each detail request
- [ ] Concurrent readers never see partial JSON and last-good data survives refresh failure
- [ ] Disk/Redis freshness semantics agree without fabricated age zero
- [ ] Unknown IDs cannot cause unbounded locks/cache or multiple upstream refreshes

## Validation

Thread/failure/temp-directory tests, app-instance isolation, mocked Redis TTL cases, and measured cold/warm memory/latency.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:56:22+00:00

App-owned bounded JSON generations and completed-ID index; defensive copies, last-good retention, atomic live-cache v1 with explicit timestamps and durable disk stale fallback. Namespaced Redis timestamps replace incorrect TTL-derived age. One SQLite lease/backoff row across workers on shared disk; unknown IDs cannot fetch or allocate cache. 25 tests:24 pass/one optional skip; explicit full-data regression suite 12/12 passes. Threaded readers/writers, generation replacement, Redis expiry/age, two-app provider lease and bounded unknown IDs verified. Compile passes. Windows atomic replace transient sharing-denial fixed with bounded retry. Measurements docs/audit/repositories-2026-10-28.json: one parse, warm list347.15ms/detail8.49ms, working set249958400bytes. Cross-host ownership requires single collector; legacy CLI writer migration T007/T025 and daily quota reservation T025; live fetching remains off. No existing files/data rewritten; rollback code with cache reader compatibility, retain disk stale data.
