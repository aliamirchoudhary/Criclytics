# T009: Correct delivery and innings cricket aggregation

- Status: Implemented; local review pending
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

### Session update 2026-10-28T09:21:14+00:00

Branch work/t009-cricket-aggregation chained from e8abb42. Shared scorer, per-innings aggregation, safe versioned streaming rebuild and manifest/difference report implemented. Hand fixtures and attributed 2024 final checks pass; final full-corpus candidate building separately in build/data-v2-verified. Original data preserved and not promoted. Expanded checks found transient Windows read sharing denial; bounded read retry added alongside atomic write retry. Acceptance still pending full-corpus report and final checks.

### Session update 2026-10-28T09:26:39+00:00

Shared per-innings scorer and streaming non-overwriting v2 rebuild implemented. Batter BF includes delivered no-balls, bowling legal balls exclude wides/no-balls; bowler conceded runs exclude byes/leg-byes/penalties. Allowed bowler-credit dismissals, non-striker runout, retired hurt/out, timed out, innings penalty timing, complete single-bowler maidens/miscounted overs, best/five-wicket figures, distinct Test innings/form/milestones, zero-run observed phases and super-over exclusion covered by hand tests. Draw/tie/no-result separate; Test chase likelihood unavailable. Full candidate build/data-v2-final accepts6651/6651 zero rejects:6246wins167draws175no-results63ties,4834players. All original processed file hashes unchanged; source/output/pipeline hashes verified. Difference report docs/audit/aggregation-v2-2026-10-28.json explains old405missingmatches and SC Cook highest176->117/innings11->19. Attributed 2024 final innings/Kohli/Klaasen figures cross-check ICC/BCCI, evidence docs/audit/real-scorecard-2026-10-28.json. 35tests:34pass/one optional skip, compile passes. Expanded concurrency checks required Windows shared-delete reads and bounded exponential replace retry, then suite passes. No artifacts promoted; docs/SCORING_CONTRACT.md defines schema/rules/attribution/rollback; T010 supplies ingestion schema validation and portable golden fixtures.
