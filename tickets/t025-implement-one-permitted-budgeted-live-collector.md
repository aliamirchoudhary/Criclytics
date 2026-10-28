# T025: Implement one permitted budgeted live collector

- Status: Implemented; local adapter only
- Priority: P1
- Depends on: T006,T014,T016,T017,T018
- Branch: work/t025-local-collector
- Base: T024 c42c8d6

## Problem

Per-visitor upstream requests and cached snapshots do not provide reliable shared delivery collection.

## Scope

Implement the adapter selected by T016: permitted API/browser source or honest manual scoring. A single bounded owner per match/source handles checkpoints/retries/backoff/global minute/day budgets/kill switch. Use worker deployment compatible with actual free-host availability.

## Acceptance criteria

- [x] Multiple visitors/workers never multiply collection cost
- [x] Quota exhaustion host sleep source changes and timeout stop safely with explicit stale state
- [x] Observations/revisions retain source/observed time without logging credentials
- [x] Recorded permitted fixtures drive adapter tests with no access-control/limit bypass

## Validation

Fake-clock/concurrency/quota/failure tests and an operator-run allowed sample with latency/cost counters.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Selected manual/replay adapter implemented as local CLI/library, never a provider fallback or public write API. Shared local volume coordinates leases/budgets; raw inputs/revisions are durable and retry timestamps never falsely refresh. Read-only visitors cannot collect. Capture times are worker-owned, while actual event time remains unknown unless supplied. Session/match rules and distinct participants are validated; terminal/unknown source status is explicit. Authored replay sample is agent-run, not a real human/operator latency pilot. Scope/limits/receipts/kill/resume/restore commands in LOCAL_COLLECTOR.md. Rollback stops local input and retains stores/cursors; no existing source data or cloud resources changed.

## T016 source decision (2026-10-28)

The approved adapter is local authorized manual/replay input. External HTTP/browser
collection is NO-GO; network allowlist is empty. Keep automated live measurements
unavailable until a future source clears the rights/no-card/timing gate. Build
quota/owner/cursor/failure semantics against local fixtures without a paid fallback.

### Session update 2026-10-28T13:19:20+00:00

Chained from T024 c42c8d6. T016 selects local authorized manual/replay input only; implement bounded single-owner, durable idempotent receipts/cursors, shared quotas/backoff/kill switch without external APIs or public write endpoints. Operator/human latency remains unmeasured.

### Session update 2026-10-28T13:33:32+00:00

75tests74pass/one optional skip; latest5collector tests pass. Local manual/replay-only collector adds persisted single-owner leases, immutable idempotent receipts/checkpoints, shared minute/day caps (including retries), backoff/kill/clock/mode/stale gates and server-owned capture timestamps.100read-only sample requests add0collection work; authored local replay sample has0external calls/dollars/card. Parallel worker/crash expiry/cap preservation/failure tests pass. Last-good display remains but failed/pending/budget/killed source blocks forecasts immediately. No public write endpoint/host worker/deployment. Human scoring latency and live-source SLA remain unproved; see LOCAL_COLLECTOR.md/audit/local-collector-2026-10-28.json.
