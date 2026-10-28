# Cloudflare Workers static frontend deployment

## Missing dist failure

The reported build installs Python requirements, then immediately executes
`npx wrangler versions upload`. `assets.directory` points to `./dist`, but that
ignored directory does not exist in a fresh Git checkout. Installing dependencies
does not generate the frontend. The missing build step caused the upload failure.

## Dashboard settings

Open the existing **criclytics Worker → Settings → Build**. Use repository root
as the Root directory (leave it empty when empty means the repository root).
Set these commands:

| Setting | Command |
|---|---|
| Build command | `python -m scripts.build_frontend` |
| Deploy command (production) | `npx wrangler@4.152.0 deploy` |
| Preview / non-production deploy command | `npx wrangler@4.152.0 versions upload` |

Keep `assets.directory` as `./dist` in `wrangler.jsonc`. Use a Python 3.11+
build image. The static build itself needs only Python's standard library;
automatically installing backend requirements is unnecessary for this step but
was not the cause of the reported error. Backend deployment remains on HF.

Save the settings, select the commit containing this fix (or merge the fix into
the intended connected branch), and retry the build. The log must show the build
command creating `dist` before Wrangler scans/uploads assets. A preview version
upload is not a production promotion. Keep production deployment on reviewed main
releases; dev/fix branches should use preview builds.

Cloudflare documents the dashboard Build command separately and currently says
Workers Builds does not honor Wrangler Custom Builds. Therefore adding a
`build.command` to the repository alone must not be assumed to repair a dashboard
build. [Cloudflare build configuration](https://developers.cloudflare.com/workers/ci-cd/builds/configuration/)
(checked 2026-10-28).

## Direct CLI deployment

For direct CLI usage, `wrangler.jsonc` now declares
`build.command = "python -m scripts.build_frontend"`. Wrangler generates the
frontend before validating/uploading it. The hook also covers `versions upload`.
[Wrangler Custom Builds](https://developers.cloudflare.com/workers/wrangler/custom-builds/).

From a clean checkout with no generated `dist/`:

```powershell
npx wrangler@4.152.0 deploy --dry-run
```

This validates/builds locally without publishing. Use the corresponding deploy
or versions-upload command only when publishing is authorized. Do not manually
prebuild and then rerun a CLI command that invokes the hook: the current builder
deliberately refuses nonempty output so unknown private files cannot survive in
the public artifact. Use a fresh checkout/output for repeat verification.

Never change the assets directory to `.` or commit `dist/` to bypass the failure.
Only the generated 17 HTML pages, static assets and public headers belong in the
upload. Secrets, raw data, model files and backend source stay outside it.

## Verification boundary

Local tests and Wrangler dry-run evidence belong in T013a. Dashboard settings and
actual Cloudflare upload success require operator verification; no account
setting or live production deployment is implied by a local dry-run. Wider T013
security/release prerequisites remain separate.
