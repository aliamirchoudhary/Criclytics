# T041A — Fix pre-plan audit findings

Status: Implemented locally, awaiting review. Branch: `fix/pre-plan-audit-findings` from audit commit
`d7a1599`. Dependencies: T041 and the pre-plan audit. This cleanup precedes T042.

Scope: address A01–A12 in docs/PRE_PLAN_AUDIT.md without new data collectors,
prediction promotion, data regeneration, account changes or deployment.

Acceptance:
- Retired collectors/model loaders cannot fetch, rewrite metadata or deserialize
  pickle; retain historical explanations outside the runtime/public packages.
- Data reads never cross selected generations. Default startup does not silently
  choose old data. Explicit archive compatibility remains available locally.
- Direct and staged container contexts exclude private artifacts; runtime uses
  a non-root user and a pinned base. Release tooling verifies remote inventory
  without deleting existing resources or exposing names of suspicious files.
- Remove inactive frontend implementations from public output; preserve current
  page/API routes and migrate internal callers/tests with code extraction.
- Triage unused Python bindings, split domain routes and pipeline exporters,
  preserve cricket statistical contracts, and report actual feature readiness.
- Add no-cost frontend CI checks and update current operator documentation.
- Pass focused regression checks, full suite, compilation, JS syntax, staging
  and mobile/desktop browser checks. Record limitations and per-finding evidence.

No push/merge/deployment or credential rotation is part of this ticket.

Acceptance evidence (2026-10-29): all A01–A12 have local code/documentation
remediation recorded in docs/AUDIT_REMEDIATION.md. Full suite: 115 tests, 114 passed, one
optional skip; isolated F/E9 lint zero; compilation and all seven active JS syntax
checks pass. Clean builds: 19 pages / 148 frontend files / 234 backend files, no staged
private artifacts or archived code. Fictional-fixture browser: 38 cases across
375/1440px includes menu/search interactions; zero page errors, HTTP failures or
document overflow. Adversarial DOM text/media and enforced-CSP assertions pass.

All 38 pipeline function ASTs remain identical through extraction; the API
function comparison changes only the intended get_series error boundary.
Archived frontend source text is preserved, normalized only for checkout line
endings. Models and original data were not regenerated or promoted.

Limits: Docker CLI is installed but its daemon is unavailable, so image execution
is unverified. Remote inventory guard and CI configuration are tested locally,
not executed against hosting. Credential rotations, hosted rollout and Git
publication/integration remain operator work. T042 has not been started.
