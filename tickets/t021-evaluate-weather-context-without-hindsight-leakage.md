# T021: Evaluate weather context without hindsight leakage

- Status: Implemented; weather excluded
- Priority: P2
- Depends on: T016,T019,T020
- Branch: work/t021-weather-context
- Base: T020 5740b3a

## Problem

Weather is absent and retrospective weather/forecasts issued later can leak into historical evaluation.

## Scope

Verify specific free/no-card weather endpoints and intended-use terms. Map venue coordinates/timezones; preserve forecast issue/valid/observed times, resolution/provenance/missingness. Distinguish retrospective reanalysis from deployable as-issued context; ablate heat/humidity/wind/rain feature families.

## Acceptance criteria

- [x] Usage rights and bounded call budgets cover the intended deployment
- [x] Venue UTC alignment never uses information unavailable at prediction cutoff
- [x] Unknown weather degrades safely and does not assert pitch bounce/dew
- [x] Held-out ablation records benefit/cost or excludes unhelpful features

## Validation

Timezone/availability/caching/quota fixtures and chronological model comparison. Recheck endpoint/archive limits rather than assuming all historic weather is free.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

As-of weather schema/UTC/location validation and bounded local cache implemented; weather family excluded from modelv1 for lack of eligible precise historical UTC/issued observations. Primary MET Norway terms support a possible future attributed free source with identified/cached traffic; no collector or paid fallback enabled. Open-Meteo free-service scope does not automatically clear intended commercial coaching use, and its archive starts after this sample. No actual weather/coordinate join or statistical benefit is invented; null ablation metrics and0eligible rows are an exclusion decision, not evidence weather has no signal. Future accepted coordinate mappings/forecasts and preregistered benefit testing remain pending. Rollback removes optional helpers only; baseline and serving unchanged.

### Session update 2026-10-28T12:53:51+00:00

Chained from T020 5740b3a. Open-Meteo primary terms/pricing/history reviewed2026-10-28: free access is non-commercial, archive starts~2022 and stitched historical forecast series are not complete as-issued runs. No endpoint called;2016?2018 sample lacks precise UTC/event/issued context. Implement fail-closed as-of weather contracts and exclude unproven family.

### Session update 2026-10-28T12:57:06+00:00

62tests61pass/one optional skip. Primary sources verify MET Norway future attributed public reuse/traffic conditions; Open-Meteo free service is non-commercial and its forecast archive does not cover this2016?2018 slice. No external calls/collector enabled. UTC/DST ambiguity/nonexistent times, issue/observation/cutoff, reanalysis exclusion, ranges/cache/missingness tests pass. All23,104historical rows lack eligible precise issued weather; no fabricated ablation benefit (deltas null), model unchanged. Actual venue mappings remain unavailable, not guessed. See WEATHER.md/audit/weather-2026-10-28.json; future source/coordinate collection and prospective benefit remain gates.
