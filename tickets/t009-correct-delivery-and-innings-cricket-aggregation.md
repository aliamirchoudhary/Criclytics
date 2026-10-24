# T009: Correct delivery and innings cricket aggregation

- Status: Planned
- Priority: P0
- Depends on: T008
- Branch: fix/t009-correct-delivery-and-innings-cricket-aggregation
- Base: latest dev

## Problem

Test innings are collapsed into match totals; legal balls, batter balls, bowler runs/wickets, maidens and draws are wrong.

## Scope

Use match/innings/player/over identities and documented scoring rules for extras/dismissals. Separate Test draw/tie/no-result and format-specific venue/phase logic. Generate corrected outputs into a new version before replacing preserved local artifacts.

## Acceptance criteria

- [ ] Two Test innings stay distinct for milestones/highest/average/not-outs/form
- [ ] Legal deliveries and batter balls are independently correct
- [ ] Bowler conceded runs/credit, non-striker runout, retirement, maidens/best figures are validated
- [ ] Manifest and before/after full-corpus difference report explain changes

## Validation

Hand-calculated tiny matches plus attributed real scorecards; totals/conservation checks, super-over/multi-innings fixtures and artifact preservation checks.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
