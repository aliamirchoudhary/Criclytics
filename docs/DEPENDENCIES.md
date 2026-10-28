# Dependency lock and verification

`requirements.in` declares direct runtime dependencies and explicit security
pins. `requirements.txt` is the cross-platform, hash-locked installation input
used by Docker and CI. Keep the scientific stack stable while upgrading the
seven packages implicated by the previous advisory snapshot.

Regenerate using uv 0.11.28:

```powershell
uv pip compile requirements.in --python-version 3.11.9 --universal --generate-hashes --output-file requirements.txt
```

Install into a fresh virtual environment with
`python -m pip install --require-hashes -r requirements.txt`, then `pip check`.
The tested interpreters are CPython 3.11.9 and 3.12.3; use a maintained patch
release, not an early 3.11 patch (soupsieve requires 3.11.5 or later).

T002 used isolated `build/env311` and `build/env312`; the original virtual
environment and model/data artifacts were preserved. Both clean installs were
synced from the same hashed lock. CI now has a 3.11/3.12 test matrix. Linux CI
execution and the Docker engine run remain separate deployment checks.

The 2026-10-28 pip-audit 2.10.1 run reports no known vulnerabilities. See
`docs/audit/dependencies-2026-10-28.json`. A zero-advisory scan is a dated result,
not proof that dependencies cannot have undiscovered or unreachable defects.
Do not blanket-ignore future findings. Run audit tools in a separate environment
so they cannot silently change runtime locks; the release workflow pins the audit
and HF uploader CLI versions. No global Python/Codex configuration was changed.
