# Branches and ticket execution

`main` is the release branch. `dev` is the integration branch, cut from main.
Each ticket uses a short-lived branch cut from the latest local/remote dev:
`fix/t002-dependencies`, `feat/t018-delivery-events`, etc. PRs target dev.
A reviewed release PR promotes dev into main; only main may deploy publicly.

This task created local `dev` and `chore/audit-and-flask-structure` from local main
`ef7c279`. They have not been pushed. Main's pre-existing one-commit difference
from origin was preserved. Do not imply remote branches/protections already exist.

```powershell
git switch dev
git pull --ff-only origin dev  # after the remote dev branch exists
git switch -c fix/t002-dependencies
```

Use a clean working tree or explicitly preserved changes before switching. The
current restructuring changes must be committed/reviewed on their current branch
before beginning another ticket. Do not reset, stash, overwrite or stage unrelated
user work. Prefer explicit files when staging. No force pushes to main/dev.

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

Operator setup still required: push dev once approved, choose dev as the default
PR base if desired, protect main/dev against direct/force pushes, require checks
and review where the account supports it, and restrict release secrets to main.
Do not assume a paid GitHub feature or secret environment is available. T001
credential rotation must happen without posting values in tickets or logs.
