# T006: Extract safe data repositories and bounded cache refresh

- Status: Planned
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
