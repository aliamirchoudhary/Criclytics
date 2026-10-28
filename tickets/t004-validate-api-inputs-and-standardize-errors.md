# T004: Validate API inputs and standardize errors

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T000
- Branch: fix/t004-validate-api-inputs-and-standardize-errors
- Base: latest dev

## Problem

Malformed limits produce 500, negative/unbounded values bypass limits and POST payload shapes are unchecked.

## Scope

Centralize bounded pagination/offset, format/metric/entity/ID/body validation and structured errors. Return generic client errors with request IDs; keep exception details in redacted internal logs. Migrate callers with contract changes.

## Acceptance criteria

- [ ] Invalid negative malformed and huge numbers yield deliberate 400 responses
- [ ] Arrays/scalars/missing fields/non-JSON prediction POST bodies are rejected
- [ ] Unknown resources and missing datasets have documented distinct semantics
- [ ] No traceback or provider URL/credential is exposed in responses

## Validation

Table-driven endpoints for numeric/string/body/size boundaries, valid callers, 400/404/413/415 responses and missing-data cases.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:42:18+00:00

17 tests discovered, 16 passed and optional original-data test skipped. Added boundary/type/format/size/duplicate-key/error-redaction tests. Inputs reject before data/provider access; missing artifacts=503, unknown=404, malformed=400, unsupported media=415, size=413. Errors include request IDs with generic internal failures. Success representations preserved; prior soft-error 200 responses deliberately retired per docs/API_CONTRACT.md.
