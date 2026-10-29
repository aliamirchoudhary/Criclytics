# T037: Context availability and annotation workflow

- Status: Tooling implemented locally; real observations/ablation pending
- Branch: feat/t037-context-availability
- Base: ff4c16c
- Depends on: T034,T023
- Budget: $0; no card or metered fallback

Provide versioned source/timing-aware weather/home/fielding/captaincy context and hypothetical notes. Missing/conflicting values remain unknown. No pressure or politics coefficient without labelled evidence and ablation.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Extended immutable context records with bounded observed weather, sourced
captaincy and prior-attempt crowd events; attribution/reuse basis mandatory.
Atomic offline import, read-only local public-scope evidence API and family
unknown/conflict/expiry summaries implemented. As-issued selection requires actual
platform ingestion time. No notes, owner IDs, writes or model coefficients in API.
Scenario UI links the existing private hypothetical-plan workflow without sending
assumptions to the model. See docs/CONTEXT_AVAILABILITY.md.

101tests100pass/one optional skip; authored fixtures cover weather conflict/expiry,
same-attempt exclusion, all-or-none import, private/remote scope and backfill.
Compilation and changed JS syntax pass. No real fielding/crowd/weather cohort or
reviewed ablation exists, so context effects remain disabled. No deployment,
network collection, billing or remote Git change.
