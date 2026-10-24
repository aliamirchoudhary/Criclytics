# T028: Build truthful live prediction workspace

- Status: Planned
- Priority: P1
- Depends on: T011,T012,T027
- Branch: feat/t028-build-truthful-live-prediction-workspace
- Base: latest dev

## Problem

Live labels/probability bars omit feed lag cutoff missing context model identity and corrections.

## Scope

Build current-score/striker/bowler panels with next-delivery distributions, lag/cutoff/revision/model identity, context coverage and issued-forecast history. Separate live/delayed/manual/replay modes and handle corrections/reconnect/abstention accessibly.

## Acceptance criteria

- [ ] Every displayed prediction links to a real issued ledger entry and pre-delivery state
- [ ] Users can distinguish fresh delayed unavailable manual and replay states
- [ ] No duplicate browser heuristic or hidden missing context
- [ ] Mobile keyboard and reduced-motion flows work under slow/error connections

## Validation

Browser scripted replay/correction/disconnect fixtures, accessible announcements and request-count checks.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
