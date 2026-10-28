# T002: Upgrade vulnerable dependencies and verify compatibility

- Status: Implemented; local review pending
- Priority: P0
- Depends on: T000
- Branch: fix/t002-upgrade-vulnerable-dependencies-and-verify-compatibility
- Base: latest dev

## Problem

pip-audit reported 25 entries, deduplicated to 16 package/advisory pairs across seven pinned packages.

## Scope

Review docs/audit/dependency-findings.json; select compatible fixed releases and a reproducible lock. Align CI/Docker versions and separate direct requirements where useful. Review flask-cors HTTP/header behavior across upgrades.

## Acceptance criteria

- [ ] Fresh installs pass pip check on Python 3.11 and 3.12
- [ ] Security scan has no applicable unresolved advisory or has an individually reviewed expiring exception
- [ ] Offline API/CORS/page tests pass against selected versions
- [ ] Release gate uses reproducible tool/requirements versions without blanket ignores

## Validation

Fresh environment install, pip check, pip-audit saved evidence, regression suite and optional model import smoke. Do not blindly choose the oldest listed fix.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Not started.

### Session update 2026-10-28T08:32:26+00:00

Verified hash-locked fresh installs on CPython 3.11.9 and 3.12.3; uv pip check passes on both. Regression suite passes (13 discovered, optional legacy-data test skipped); model imports pass. pip-audit 2.10.1 reports no known vulnerabilities. Docker/CI consume hashed requirements; CI matrix added. See docs/DEPENDENCIES.md and dated advisory JSON. No model/data artifacts were regenerated.
