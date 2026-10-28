# T013: Verify CI deployment artifacts branch controls and rollback

- Status: Blocked; T001 operator prerequisite
- Priority: P1
- Depends on: T001,T002,T003,T010
- Branch: fix/t013-verify-ci-deployment-artifacts-branch-controls-and-rollback
- Base: latest dev

## Problem

New workflows/staging have not run on real hosts; original deployment lacked upload boundaries and remote protections are unverified.

## Scope

Harden new CI with explicit Python matrix and reviewed pinned tooling/actions; verify separate dataset restore and frontend output. Operator sets remote dev/main protections supported by free account, verifies HF/Cloudflare settings and performs release/rollback without uploading checkout or deleting data.

## Acceptance criteria

- [ ] Clean-clone offline checks/security gate pass on supported Python versions
- [ ] Build manifests exclude env/Git/raw/private/venv artifacts
- [ ] Only reviewed main releases access publishing secrets; task PRs target dev
- [ ] Operator records staging/deployed smoke and tested rollback/restore; no paid feature assumed

## Validation

Artifact inspections, container/staging smoke where runtime exists, CI run and operator host checks. No remote push/deploy/account change without authorization.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

The independently scoped [T013a](t013a-cloudflare-assets-build.md) addresses the
reported missing-dist failure. Its local build verification does not complete
this ticket's wider security, account policy, release or rollback prerequisites.

### Session update 2026-10-28T11:58:30+00:00

T001 credential rotation and production containment checks remain explicitly deferred by user. T013 production release/rollback acceptance cannot proceed; no remote Git mutations permitted. Continue independent T014; no deployment attempted.
