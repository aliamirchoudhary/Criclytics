# T012: Consolidate frontend initialization and API configuration

- Status: Planned
- Priority: P2
- Depends on: T003,T005,T011
- Branch: fix/t012-consolidate-frontend-initialization-and-api-configuration
- Base: latest dev

## Problem

Global inline scripts/ML initializers duplicate requests/renderers, compete for DOM state and hardcode production routing.

## Scope

Extract shared API/config/DOM helpers and one data initialization path per page; use backend validated inference contracts, remove duplicate client probabilities, extract common styles/components incrementally and preserve static hosting. Reduce legacy API/helper coupling as touched.

## Acceptance criteria

- [ ] Each page loads its data flow once without duplicate list/ML calls
- [ ] Local preview and production builds select explicit backend configuration
- [ ] No client heuristic masquerades as calibrated backend prediction
- [ ] Static and Flask builds agree and existing public URLs remain compatible

## Validation

Browser request-count/race tests, delayed/error responses, preview-origin matrix and JS/page regressions.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
