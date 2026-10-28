# T025: Implement one permitted budgeted live collector

- Status: Planned
- Priority: P1
- Depends on: T006,T014,T016,T017,T018
- Branch: feat/t025-implement-one-permitted-budgeted-live-collector
- Base: latest dev

## Problem

Per-visitor upstream requests and cached snapshots do not provide reliable shared delivery collection.

## Scope

Implement the adapter selected by T016: permitted API/browser source or honest manual scoring. A single bounded owner per match/source handles checkpoints/retries/backoff/global minute/day budgets/kill switch. Use worker deployment compatible with actual free-host availability.

## Acceptance criteria

- [ ] Multiple visitors/workers never multiply collection cost
- [ ] Quota exhaustion host sleep source changes and timeout stop safely with explicit stale state
- [ ] Observations/revisions retain source/observed time without logging credentials
- [ ] Recorded permitted fixtures drive adapter tests with no access-control/limit bypass

## Validation

Fake-clock/concurrency/quota/failure tests and an operator-run allowed sample with latency/cost counters.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

## T016 source decision (2026-10-28)

The approved adapter is local authorized manual/replay input. External HTTP/browser
collection is NO-GO; network allowlist is empty. Keep automated live measurements
unavailable until a future source clears the rights/no-card/timing gate. Build
quota/owner/cursor/failure semantics against local fixtures without a paid fallback.
