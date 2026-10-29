# T040: Coach validation and reviewed release

- Status: Offline checks passed; external acceptance/release blocked
- Branch: chore/t040-reviewed-release-gates
- Base: 4e331b1
- Depends on: T031,T034,T035,T036,T038
- Budget: $0; no card or metered fallback

Complete real coach usability/prospective evaluations, deployed containment and current credential/release gates; publish reviewed main only after explicit Git/deployment approval.

Read docs/NEXT_BALL_PLATFORM_PLAN.md and the relevant source/model/privacy instructions.
Use a new branch chained from the preceding completed ticket branch. Verify requirements
with focused tests and actual browser/measurement evidence; update this ticket and index.
Do not mark Done before review/integration, and do not fabricate external acceptance.

Fresh offline release preparation passed:19page clean frontend/backend allowlists,
13original hashes, private-path/CSP checks and authored restore/rollback drills.
Fresh locked pip-audit31packages/zero known advisories. Evidence retained at
docs/audit/release-preflight-2026-10-29.json; prior dated reports preserved. Tool
now requires explicit fresh audit/report arguments instead of silently reusing or
overwriting October28evidence. No network during smoke/restore/build checks.

Final browser matrix95page-width cases/four failure-keyboard interactions pass;
restored cricket and scenario375/1440flows pass.103unit tests102pass/one skip;
compilation/changed JS syntax pass. PLATFORM_HANDOFF_2026-10-29.md records all
local ticket branches, private artifacts, preview and acceptance limits.

Actual coach participants/prospective matches remain0. No source rights/timing
trial, rotations/containment, hosted restore/capacity or reviewed Git integration
was fabricated. Those are external blockers; release remains BLOCKED. No push,
merge, main/dev commit, deployment, resource deletion, card or billing activation.
