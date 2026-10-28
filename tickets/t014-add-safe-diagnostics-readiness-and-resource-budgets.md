# T014: Add safe diagnostics readiness and resource budgets

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T004,T006
- Branch: work/t014-safe-diagnostics
- Base: T012 e30684e; T013 gated by deferred T001

## Problem

Health says ok with missing data; no reliable request tracing, source lag or quota/capacity visibility exists.

## Scope

Add structured redacted logs/request IDs, distinct health/readiness, data/model versions, provider freshness/cache/error/quota counters and local bounded diagnostics. Measure latency distributions, payload size and memory; no paid APM.

## Acceptance criteria

- [x] Readiness distinguishes required artifact failure from optional feed degradation
- [x] No credentials/query keys/private notes leak to logs or public diagnostics
- [x] Counters distinguish cache hit quota stop stale fallback timeout and parse failure
- [x] Measured budgets and operator troubleshooting steps fit actual free hardware

## Validation

Missing/corrupt artifact tests, redaction assertions, load samples and repeatable offline diagnostic report.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented locally. Public /api/status now shares readiness semantics (503 for required artifact failure); /api/health is liveness. No caller may treat old status=ok/key-presence fields as a readiness guarantee. Local bounded diagnostics replaces directory/credential-presence output. Rollback through reviewed code change; no dataset/account changes occurred.

### Session update 2026-10-28T11:58:30+00:00

Chained branch work/t014-safe-diagnostics from T012. Read audit/architecture/workflow and T014 requirements; implement bounded redacted local diagnostics/readiness without provider calls.

### Session update 2026-10-28T12:02:06+00:00

46-test suite45pass/one optional skip. Missing/corrupt required data yields503 while liveness remains200; optional feed degradation does not fail readiness. Fixed event counters and256 samples bound telemetry; redaction tests cover query/provider/Redis/private-note sentinels. Offline20-request sample11,549bytes each, p50~108ms/p95~304ms/max451ms and~413MB resident; no provider calls. See docs/DIAGNOSTICS.md and audit/diagnostics-2026-10-28.json. Structural readiness is not hash validation; deployment/resource acceptance stays pending.
