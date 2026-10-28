# T013a: Generate frontend assets before Cloudflare upload

- Status: Implemented locally; dashboard verification pending
- Priority: P1
- Depends on: T000 (merged into origin/dev at e4f7ab4)
- Parent: T013; independent deployment hotfix, not completion of its wider scope
- Branch: fix/t013a-cloudflare-assets
- Base: dev at e4f7ab4

## Problem

The supplied Workers Builds log runs `npx wrangler versions upload` without first
generating the ignored `dist/` directory. Python dependency installation is not
a frontend build. The migration configured the upload location but omitted a
Wrangler build hook and an explicit dashboard-build setup procedure.

## Scope

Add the CLI custom-build hook, make frontend path imports independent of Flask
dependencies, verify a clean checkout build, and document the dashboard build
command. Workers Builds currently does not honor Wrangler custom builds, so the
operator must set its separate Build command. Preserve public-only output and
existing unknown-file guards. Do not deploy the Flask backend to Cloudflare or
claim the wider T013/security prerequisites are complete.

## Acceptance criteria

- [x] Clean CLI deployment generates all public assets before Wrangler validates them.
- [x] Frontend build runs using Python standard library without installing Flask/ML packages.
- [x] Existing backend/page/security regression checks pass.
- [x] Exact Workers Builds settings and pending operator verification are documented.
- [ ] Operator saves the dashboard Build command and confirms a successful preview build.

## Validation

Run the clean-copy subprocess build with `python -S`, offline tests, compilation,
and a Wrangler dry-run from a fresh temporary checkout. No live publish required.

## Implementation evidence

2026-10-28: Wrangler 4.152.0 `deploy --dry-run` in a fresh temporary checkout
executed the configured Python build, found the public assets directory, and
exited successfully without publishing. The subprocess test runs the build with
`python -S` to verify no backend site packages are needed. Unittest discovery:
13 tests run, 12 passed and the optional original-data fingerprint test skipped.
Python compilation, config duplicate-key validation and changed-document links
also passed. The existing nonempty-output/private-file guards remain intact.

Cloudflare dashboard settings cannot be changed through the available tools;
actual dashboard upload success requires the operator to set Build command to
`python -m scripts.build_frontend` and retry. See docs/CLOUDFLARE_DEPLOYMENT.md.
The branch is based on merged dev e4f7ab4; wider T013 work remains Planned.
