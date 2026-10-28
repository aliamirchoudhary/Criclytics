# T003: Remove DOM injection hazards and tighten browser policy

- Status: Implemented; local review pending
- Priority: P0
- Depends on: T000
- Branch: fix/t003-remove-dom-injection-hazards-and-tighten-browser-policy
- Base: latest dev

## Problem

Country/team/API data reaches HTML attributes and innerHTML with inconsistent escaping, including inline handlers.

## Scope

Inventory dynamic sinks; use text/attribute DOM APIs, validate remote image URL schemes/hosts, replace unsafe handlers and introduce a tested CSP strategy. Keep CORS scoped to configured API origins; it is not authentication.

## Acceptance criteria

- [ ] Adversarial name/venue/query/image values cannot execute scripts or create handlers
- [ ] Quotes/apostrophes/Unicode render correctly as text
- [ ] Headers/CSP work with actual local and CDN assets
- [ ] Bootstrap/flag/profile/search/compare sinks have regression coverage

## Validation

Browser injection fixtures, normal-page smoke, header/CORS tests. Review actual source findings SEC-05/07/11.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:39:32+00:00

Vendored DOMPurify provenance/licence, guarded legacy DOM sinks, image-host policy, apostrophe escaping and safe team fallback. Chromium adversarial tests for search/compare/profile plus contextual table rendering pass with zero injected execution. Regression suite and JS syntax pass. CSP image/object/base rules enforced; strict script policy intentionally report-only pending T012 inline migration. See docs/DOM_SECURITY.md.
