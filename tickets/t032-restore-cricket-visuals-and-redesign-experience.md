# T032: Restore cricket visuals and redesign the frontend experience

- Status: Implemented; visual review pending
- Branch: feat/t032-frontend-experience
- Base: merged origin/dev (633f41c)
- Requested by: owner after reviewing the simplified frontend

Restore the visual identity lost in T011: country flags, player portraits, useful
match cards and richer profiles. Redesign shared navigation, typography, spacing,
home discovery, filters and responsive tables across all 19 pages. Preserve API
contracts, truthful unavailable states, stable identity links, private-plan behavior,
CSP and the $0/no-card budget.

Acceptance: locally served licensed flags and attributed portraits; graceful image
fallbacks; working search/filter/profile navigation; desktop and mobile browser
evidence; no invented stats/live claims; routine regression checks. Portraits are
curated by stable identity; incomplete photo coverage must remain explicit.

No deployment, remote mutation or merge is part of this ticket.


## Implementation and verification

- Shared dark editorial design with green accents, desktop navigation/mobile
  disclosure menu, clearer search, filters, tables, tab and focus states.
- New homepage headline, locally hosted player photography, discovery links and
  independent result/fixture loading with retry. Unknown/live states remain honest.
- Flagged two-team scorecards, observed-team badges in player/team directories,
  imagery in search/records/rankings/comparisons and player profile identity panels.
- Profiles use expandable yearly/opposition/venue tables and compact recent-innings
  score strips, retaining all records and format tabs.
-105 bundled flag SVGs (MIT) and2 licensed portraits with file hashes, source/author/
  license links and exact stable-ID mapping. Unknown IDs and failed media use
  labelled initials. No AI likenesses, guessed nationality or unlicensed photo imports.
- Existing APIs, private-note behavior, data, source policy and prediction gates
  preserved. No added runtime dependency, paid service, remote push or deployment.

Evidence: docs/audit/application-ui-t032-2026-10-29.json (95 Chrome page/width cases
and4 interactions); frontend-experience-t032-2026-10-29.json (mobile/desktop menu,
filter, stable profile, tabs, expandable records, attribution, identity safety,
denied media and partial API failure); frontend-build-t032-2026-10-29.json.
Full suite:89tests,88passed/one optional legacy-data skip. Compilation, changed JS
syntax and diff whitespace checks pass. The first browser matrix found homepage
aria-busy flags remaining after loading; corrected before the passing rerun.

Local preview: http://127.0.0.1:5050. Screenshots: build/t032-preview/ (ignored).
Media provenance and extension procedure: docs/MEDIA_ASSETS.md.

Limits: only2players currently have curated portraits; a further source returned
429 and was not retried. Chrome/local evidence is not Safari/Firefox, screen-reader
speech, hosted latency or actual coach acceptance. Owner visual review is pending.
Rollback is review/revert of this ticket, retaining original data and public URLs;
no production version was changed.
