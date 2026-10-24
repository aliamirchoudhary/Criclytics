# T014: Add safe diagnostics readiness and resource budgets

- Status: Planned
- Priority: P1
- Depends on: T004,T006
- Branch: fix/t014-add-safe-diagnostics-readiness-and-resource-budgets
- Base: latest dev

## Problem

Health says ok with missing data; no reliable request tracing, source lag or quota/capacity visibility exists.

## Scope

Add structured redacted logs/request IDs, distinct health/readiness, data/model versions, provider freshness/cache/error/quota counters and local bounded diagnostics. Measure latency distributions, payload size and memory; no paid APM.

## Acceptance criteria

- [ ] Readiness distinguishes required artifact failure from optional feed degradation
- [ ] No credentials/query keys/private notes leak to logs or public diagnostics
- [ ] Counters distinguish cache hit quota stop stale fallback timeout and parse failure
- [ ] Measured budgets and operator troubleshooting steps fit actual free hardware

## Validation

Missing/corrupt artifact tests, redaction assertions, load samples and repeatable offline diagnostic report.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
