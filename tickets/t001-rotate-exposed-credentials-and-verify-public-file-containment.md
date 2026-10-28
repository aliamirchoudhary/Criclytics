# T001: Rotate exposed credentials and verify public-file containment

- Status: Waiting for operator
- Priority: P0
- Depends on: T000
- Branch: fix/t001-rotate-exposed-credentials-and-verify-public-file-containment
- Base: latest dev

## Problem

Old local GET requests expose .env/Git files; a credential-like literal exists in tracked debug-script history.

## Scope

Operator-led containment: deploy the reviewed boundary fix, review exposed credential categories and uploaded files/logs, revoke/rotate where applicable, and decide whether coordinated history cleanup is warranted. Never print secrets or rewrite history autonomously.

## Acceptance criteria

- [ ] Operator records credential categories/actions/times with values redacted
- [ ] Public source/config/Git/data paths are blocked on the actual host after release
- [ ] Remote HF artifacts are reviewed for previously uploaded secrets
- [ ] Historical literals are treated as compromised after current-file removal

## Validation

Local exposure regression plus operator-run production checks without downloading/printing secrets. This blocks public release; pending operator work does not block independent local fixes.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:30:47+00:00

Local containment and secret-storage exclusions retained. HEAD-only production checks are inconclusive (fallback status responses/timeouts); no secret bodies retrieved. Provider rotations and HF login require the owner. See docs/AUTHENTICATION.md. Local work does not complete production acceptance.
