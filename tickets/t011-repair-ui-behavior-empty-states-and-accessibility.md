# T011: Repair UI behavior empty states and accessibility

- Status: Planned
- Priority: P1
- Depends on: T004,T007,T008
- Branch: fix/t011-repair-ui-behavior-empty-states-and-accessibility
- Base: latest dev

## Problem

Team crest fallback throws at both widths; unlabelled controls, placeholder actions/data and incomplete states remain.

## Scope

Fix detached-parent image fallback; inventory all 17 pages and their actions/filters/tabs. Remove unsupported Follow/demo actions or implement intended local behavior. Label historical coverage, stale data and missing values; repair entity links, accessible names and focus semantics.

## Acceptance criteria

- [ ] Team profile handles denied images with no uncaught error
- [ ] All visible inputs have accessible names and core flows work by keyboard/touch
- [ ] Loading empty unknown error and stale states never show believable fake metrics
- [ ] 320/375/768/1024/1440 widths handle controls/long names/tables with no unintended clipping; contrast/reduced motion reviewed

## Validation

Browser interaction matrix, denied-image/API-failure fixtures, keyboard walkthrough and documented screen-reader/contrast checks. Split explicit child tickets if inventory exceeds a reviewable PR.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
