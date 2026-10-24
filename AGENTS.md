# Working in Criclytics

Read `docs/AUDIT.md`, `docs/ARCHITECTURE.md`, `docs/GIT_WORKFLOW.md`, and the active
file in `tickets/` before implementing a ticket. `tickets.md` is the index.

- Work on one ticket branch from dev. Main is release-only. Preserve unrelated
  changes and original artifacts; do not rewrite history without authorization.
- The budget is $0 with no credit card. No metered fallback, paid API, paid LLM,
  GPU dependency or billing activation. Verify source rights and limits before
  implementing collectors. Never bypass access controls or provider limits.
- Keep secrets, raw data and model artifacts outside public static output. Never
  log credentials, provider URLs containing keys, or private coach notes.
- Do not claim validated ML predictions until chronological held-out evaluation
  and calibration exist. Missing data means unavailable, not an invented 50%.
- Public URLs/API callers must migrate together. Use the Flask factory/blueprints
  and paths module. Run CLI modules with `python -m ...`.
- Routine checks: `python -m unittest discover -s tests -v`, Python compilation,
  and `node --check` for changed JS. Use local-data regression fingerprints only
  while deliberately preserving legacy behavior; update/retire them with an
  explained statistical contract change, never simply to silence failures.
- Browser audit is optional tooling under `tools/`. Reproduce relevant UI states
  at mobile/desktop widths and include errors/limitations. Do not treat a passing
  file/link check as functional UI acceptance.
- Update the active ticket and index with evidence. Complete dependencies before
  dependent tickets. Do not start the whole roadmap in one implementation.
