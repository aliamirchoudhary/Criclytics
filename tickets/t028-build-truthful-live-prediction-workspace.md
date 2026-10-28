# T028: Build truthful live prediction workspace

- Status: Implemented, awaiting review
- Priority: P1
- Depends on: T011,T012,T027
- Branch: work/t028-prediction-workspace
- Base: preceding local ticket branch (resumed-session user override)

## Problem

Live labels/probability bars omit feed lag cutoff missing context model identity and corrections.

## Scope

Build current-score/striker/bowler panels with next-delivery distributions, lag/cutoff/revision/model identity, context coverage and issued-forecast history. Separate live/delayed/manual/replay modes and handle corrections/reconnect/abstention accessibly.

## Acceptance criteria

- [x] Every displayed prediction links to a real issued ledger entry and pre-delivery state
- [x] Users can distinguish fresh delayed unavailable manual and replay states
- [x] No duplicate browser heuristic or hidden missing context
- [x] Mobile keyboard and reduced-motion flows work under slow/error connections

## Validation

Browser scripted replay/correction/disconnect fixtures, accessible announcements and request-count checks.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Implemented for default-off local shadow review; public live feed/model promotion remain unavailable.

### Session update 2026-10-28T17:14:59+00:00

Chained from T027 local commit. Build explicit manual/replay/unavailable workspace tied to issued ledger records, no public live feed or model promotion.

### Session update 2026-10-28T17:21:10+00:00

18th allowlisted/static-build page workspace.html, shared navigation/renderer/CSP. Manual/replay/unavailable modes, score/announced actors/source age/cutoff/revision/model/sample/context coverage; current distribution links to real issued history, replacement links retained, no heuristic. Manual refresh makes two workspace reads; current eligibility expires without polling and subtracts history network delay. Browser375/1440 keyboard/reduced-motion/correction/stale/error-retry/slow/replay/disabled/actual15sec expiry pass. All18pages at320/375/768/1024/1440:90cases+4interactions pass.84tests83pass/one optional skip, compilation/JS syntax pass. Updated explicit static page count17->18; independent PAGES allowlist parity check retained. Evidence workspace-ui and application-ui-t028 JSON; WORKSPACE_UI.md. Authored local source/model, no real coach/feed trial, promotion or deployment.
