# T016: Prove permitted zero-budget live data feasibility

- Status: Implemented; replay/manual decision
- Priority: P1
- Depends on: T015
- Branch: work/t016-free-feed-feasibility
- Base: T015 1c3b5d3

## Problem

Minute-level cached scores and a once-daily scorecard gate cannot support timely next-delivery forecasts; no compliant free source is proven.

## Scope

Compare explicitly allowed APIs/public feeds, permitted browser automation and manual scoring. Record dated primary terms/redistribution/card/quotas/coverage/latency/revisions/worker constraints. Run only bounded authorized experiments; no authentication/paywall/CAPTCHA/rate-limit bypass.

## Acceptance criteria

- [x] Matrix proves $0/no-card/reuse rights or rejects/marks unknown each candidate
- [ ] Allowed sample measures lag missed deliveries corrections and quota use
- [x] Playwright memory/selector fragility and free-host sleep are considered
- [x] Explicit go/no-go selects feed or replay/manual mode and gates collector work

## Validation

Dated source terms, redacted events, bounded latency/coverage experiment and honest fallback decision. No guarantee that a suitable legal free live feed exists.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Local feasibility decision implemented; review pending. Primary references and exact unknowns are recorded in docs/LIVE_FEASIBILITY.md. A real external live sample is intentionally NOT checked off: no permitted source was established, so all actual external lag/coverage/revision fields remain null. Fictional replay demonstrates timing failure modes without implying a live benchmark or human-scorer pilot. This is the explicitly supported no-go/fallback outcome; T025 can implement authorized local manual/replay mode, while external feed proof remains an open future gate. No account/credential changes or real API calls. Rollback must not re-enable unapproved network sources; retain historical reads/manual mode.

### Session update 2026-10-28T12:10:43+00:00

Chained from T015 1c3b5d3. Dated primary source terms/free-tier review; no existing credential use or provider polling. Choose only proven no-card reuse path, otherwise replay/manual fallback.

### Session update 2026-10-28T12:15:39+00:00

Primary dated terms/pricing matrix rejects unproven automated feeds and selects historical replay/local authorized manual scoring. Empty network allowlist enforced in legacy web refresh and CLI source primitives; flags/keys cannot grant rights.49tests48pass/one optional skip; synthetic36delivery/one-correction timing experiment uses zero external calls and records selector fragility/renderer heap. Real external lag/missed-delivery/correction measurements remain unavailable, not claimed. See LIVE_FEASIBILITY.md and audit/live-feasibility-2026-10-28.json. T025 may proceed only with selected local manual/replay adapter; live proof remains open.
