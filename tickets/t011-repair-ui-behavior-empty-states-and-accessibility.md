# T011: Repair UI behavior empty states and accessibility

- Status: Implemented; local review pending
- Priority: P1
- Depends on: T004,T007,T008
- Branch: work/t011-ui-accessibility
- Base: work/t010-golden-schema-contracts (046ada4), chained per session authorization

## Problem

Team crest fallback throws at both widths; unlabelled controls, placeholder actions/data and incomplete states remain.

## Scope

Fix detached-parent image fallback; inventory all 17 pages and their actions/filters/tabs. Remove unsupported Follow/demo actions or implement intended local behavior. Label historical coverage, stale data and missing values; repair entity links, accessible names and focus semantics.

## Acceptance criteria

- [x] Team profile handles denied images with no uncaught error
- [x] All visible inputs have accessible names and core flows work by keyboard/touch
- [x] Loading empty unknown error and stale states never show believable fake metrics
- [x] 320/375/768/1024/1440 widths handle controls/long names/tables with no unintended clipping; contrast/reduced motion reviewed

## Validation

Browser interaction matrix, denied-image/API-failure fixtures, keyboard walkthrough and documented screen-reader/contrast checks. Split explicit child tickets if inventory exceeds a reviewable PR.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented locally; review/integration pending. See docs/UI_ACCEPTANCE.md for the action inventory, evidence, limitations and rollback.

### Session update 2026-10-28T10:00:50+00:00

New shared data-driven accessible surfaces replace retained demo regions across17 publicURLs; original markup archived docs/history/ui-pre-t011. Navy/blue visual identity preserved. 85 real-data Chrome cases at320/375/768/1024/1440 pass without pageerrors/unnamed visible controls/loading leftovers/documentoverflow. Denied-image fallback, keyboardtabs, missing/unknown/empty/API503 states pass. Targeted pagination/teamcomparison, malicious longnames atallfivewidths, zero-vs-null and reduced-motion checks pass; selected contrastpairs >=4.5. Full40-test suite39pass/one optionalskip. Remaining work: final action inventory/docs/tool handoff; screen-reader speech and cross-browser checks explicitly unverified.

### Session update 2026-10-28T10:07:22+00:00

Final verification: 41 unit tests (40 passed, one optional skip); 85 Chrome page/width cases passed; denied-image, keyboard tabs, empty/unknown/503, pagination, team comparison, malicious long names, zero/null and reduced-motion checks passed. Selected contrast pairs exceed 4.5:1. See docs/UI_ACCEPTANCE.md and audit/application-*. No deployment. Stop requested after this ticket; T012 not started.
