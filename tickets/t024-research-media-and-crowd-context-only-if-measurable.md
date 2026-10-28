# T024: Research media and crowd context only if measurable

- Status: Implemented; optional research excluded
- Priority: P3
- Depends on: T015,T020,T023
- Branch: work/t024-media-research
- Base: T023 c0a2acc

## Problem

Negative media or booing does not establish a measurable psychological state or useful independent predictive signal.

## Scope

Preregister a bounded experiment with permitted timestamped $0 public/manual data. Define observable labels, source coverage, language bias, confounding and strict cutoffs. No required paid LLM/social feed or mental-health/personality inference.

## Acceptance criteria

- [x] Legal access and reproducible observable labels are documented
- [x] Subjective pressure is an uncertain proxy rather than ground truth
- [x] As-of ablation can conclude no signal and exclude the feature
- [x] Research does not block baseline historical analytics or live launch

## Validation

Reviewed experiment plan, annotation agreement, chronological leakage/confounding and cost report; no production feature until evidence supports it.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Optional research protocol and fixture-only validators implemented; feature excluded. Observable source-attributed labels differ from subjective pressure/mental state. Real independent-rater agreement and predictive as-of ablation are unproved, not replaced by synthetic agreement statistics. Source/time/identity/rights and fixed72hour media-window guards are tested. GDELT dataset terms are documented without assuming rights to linked articles/broadcasts or enabling BigQuery/billing. Future bounded prospective pilot and fresh held-out comparison are preregistered; no production feature or launch dependency added. Rollback retains research docs/evidence and no active model change.

### Session update 2026-10-28T13:12:42+00:00

Chained from T023 c0a2acc. Preregister bounded observable-media/crowd experiment with authored/authorized local data only; no paid LLM/social API or inferred mental state. Real annotation agreement/causal/predictive benefit unavailable, so feature remains excluded and cannot block core launch.

### Session update 2026-10-28T13:16:34+00:00

70tests69pass/one optional skip. Preregistered ed4a874 bounded observable-proxy plan documents manual/GDELT dataset rights, unknown source-specific collection/coverage, language/confounding/as-of controls and no psychological ground truth. Authored-fixture agreement arithmetic and cutoff/unknown/rights guards pass; real raters/agreement/benefit remain null. No paid LLM/social feed/collector or production proxy enabled; optional P3 research does not block core launch. See MEDIA_RESEARCH_PROTOCOL.md/audit/media-research-2026-10-28.json.
