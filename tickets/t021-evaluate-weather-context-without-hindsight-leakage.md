# T021: Evaluate weather context without hindsight leakage

- Status: Planned
- Priority: P2
- Depends on: T016,T019,T020
- Branch: feat/t021-evaluate-weather-context-without-hindsight-leakage
- Base: latest dev

## Problem

Weather is absent and retrospective weather/forecasts issued later can leak into historical evaluation.

## Scope

Verify specific free/no-card weather endpoints and intended-use terms. Map venue coordinates/timezones; preserve forecast issue/valid/observed times, resolution/provenance/missingness. Distinguish retrospective reanalysis from deployable as-issued context; ablate heat/humidity/wind/rain feature families.

## Acceptance criteria

- [ ] Usage rights and bounded call budgets cover the intended deployment
- [ ] Venue UTC alignment never uses information unavailable at prediction cutoff
- [ ] Unknown weather degrades safely and does not assert pitch bounce/dew
- [ ] Held-out ablation records benefit/cost or excludes unhelpful features

## Validation

Timezone/availability/caching/quota fixtures and chronological model comparison. Recheck endpoint/archive limits rather than assuming all historic weather is free.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.
