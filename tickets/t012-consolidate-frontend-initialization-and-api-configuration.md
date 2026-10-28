# T012: Consolidate frontend initialization and API configuration

- Status: Implemented; local review pending
- Priority: P2
- Depends on: T003,T005,T011
- Branch: work/t012-frontend-runtime
- Base: T011 a3d445a, chained per user authorization

## Problem

Global inline scripts/ML initializers duplicate requests/renderers, compete for DOM state and hardcode production routing.

## Scope

Extract shared API/config/DOM helpers and one data initialization path per page; use backend validated inference contracts, remove duplicate client probabilities, extract common styles/components incrementally and preserve static hosting. Reduce legacy API/helper coupling as touched.

## Acceptance criteria

- [x] Each page loads its data flow once without duplicate list/ML calls
- [x] Local preview and production builds select explicit backend configuration
- [x] No client heuristic masquerades as calibrated backend prediction
- [x] Static and Flask builds agree and existing public URLs remain compatible

## Validation

Browser request-count/race tests, delayed/error responses, preview-origin matrix and JS/page regressions.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Shared runtime config/API/DOM modules replace active legacy globals. Static builder and Flask generate identical public config; HTTPS origin validation rejects credentials/paths/queries/control characters, with loopback HTTP only for local development. Empty explicitly means same-origin. Runtime config is no-store, GETs coalesce only while in flight, timeout at15 seconds, and failed requests remain retryable. Match detail no longer uses server bootstrap; initialization is idempotent and filter generations reject stale responses. Active CSS has no external dependencies. Script CSP is enforced without inline/external scripts; legacy public assets remain unloaded for URL compatibility.

43 unit tests (42 pass/one optional skip); request-count checks on all17 pages, duplicate script injection, delayed response race, failure retry and synthetic preview/production/local routing passed. See docs/audit/frontend-runtime-2026-10-28.json. Compilation/changed JS syntax passed. No deployments or dashboard changes. Static Cloudflare builds must set the documented FRONTEND_API_BASE public variable before release. Rollback: restore T011 templates/renderer/policy together through a reviewed change; keep new config out of secrets. Responsive matrix completion recorded in final session update.

### Session update 2026-10-28T11:50:51+00:00

Resumed on chained branch work/t012-frontend-runtime from T011 a3d445a. Consolidate runtime configuration, one request/render path, static/Flask parity and enforced script policy.

### Session update 2026-10-28T11:58:18+00:00

Final85-case responsive matrix and four targeted failure/keyboard cases pass under enforced CSP. Updated browser helpers use function waits compatible with strict CSP; targeted interaction suite also passes after verifying zero/null display. Full43-test suite42pass/one optional skip; static/Flask byte parity and origin safety pass. No deployment. Configure FRONTEND_API_BASE for static releases per docs/CLOUDFLARE_DEPLOYMENT.md.
