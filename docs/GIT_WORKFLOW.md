# Branches and ticket execution

`main` is the release branch. `dev` is the integration branch, cut from main.
Each ticket uses a short-lived branch cut from the latest local/remote dev:
`fix/t002-dependencies`, `feat/t018-delivery-events`, etc. PRs target dev.
A reviewed release PR promotes dev into main; only main may deploy publicly.

The initial repository migration setup is historical; it does not establish
current remote branch/protection state. For the present resumed session, the
explicit user override below applies: chain a **new** local branch from the
previous branch and commit there under aliamirchoudhary. Never commit on dev/main
or push, merge, rebase, reset, tag or change PRs without explicit approval.
Preserve unrelated work and inspect the tree before switching/staging.

For every implementation:

1. Read `AGENTS.md`, the ticket, its dependencies, and relevant audit findings.
2. Record the starting branch/base and set the ticket to In progress.
3. Implement only its scope. Preserve contracts or document/migrate callers.
4. Run its checks plus relevant existing regression tests. Network/paid services
   must not be required by routine CI.
5. Update the ticket with exact changes, evidence, remaining issues and status.
6. Create a focused commit/PR against dev when publication is authorized. Include
   problem, result, validation, limitations and migration/rollback details.
7. Mark Done only after acceptance evidence is reviewed and integrated. Work in
   the current branch can be marked Implemented, awaiting review.

Remote settings must be inspected before claiming protection. Choose dev as the default
PR base if desired, protect main/dev against direct/force pushes, require checks
and review where the account supports it, and restrict release secrets to main.
Do not assume a paid GitHub feature or secret environment is available. T001
credential rotation must happen without posting values in tickets or logs.

## Resumed-session user override (2026-10-28)

The user explicitly authorizes sequential local ticket branches chained from the
previous ticket branch and local commits exclusively on those newly created
branches. This overrides the normal dev-base rule for this session. Do not push,
merge, rebase, reset, tag, change PRs or mutate remote repositories. The operator
will review/integrate the final branch into dev. See SESSION_PROGRESS.md for chain
and pending external acceptance. No commits on main, dev, or pre-existing branches.
