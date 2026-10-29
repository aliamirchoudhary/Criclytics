# T041B — Targeted presentation polish before platform expansion

Status: Implemented, awaiting review/integration. Branch: `fix/t041b-presentation-polish` from `7fb9f0c`.
Dependency: T041A. User authorizes committing and pushing these fixes; no merge
or deployment is requested. The broad UI redesign remains deferred.

Acceptance: restore a full footer using main's links and Kryzect credit on all
pages; entity/match card surfaces navigate to their detail pages while retaining
secondary actions; move concise dataset/mode notes below main content; present
ML findings and joint outcomes in plain cricket language; name each comparison
probability panel; space scouting actions; show a single genuine empty search
state instead of empty category notices alongside results. Preserve honest
experimental limits, privacy, public routes and statistics. Verify mobile/desktop
interaction, full tests, JS syntax, compilation and builds. Record evidence.

Implemented: all 19 pages have a four-column responsive footer with original
main's platform/tools/information links, Disclaimer, Contact and Kryzect branding.
Concise coverage and replay/manual notes moved below content. Native stretched
card links cover player/team/venue/match cards; secondary actions remain separate.
ML summaries explain cricket inputs, historical findings and live-use limits
without hashes, raw evaluation tables or developer jargon. Comparison probability
sections name their player; scenario outcomes render as readable cricket events.
Scouting export controls have responsive spacing. Empty search categories are
omitted; truly empty searches have one explanatory state.

Verification: 115 tests, 114 pass and one optional skip; compilation, changed-JS
syntax and clean frontend/backend builds pass. Playwright: 14 targeted checks
against the configured local preview, including actual scenario calculation,
at 375px/1440px; all 19 pages at both widths (38 additional cases) have no page
errors, HTTP failures or horizontal document overflow. Footer screenshots
inspected at both sizes. Evidence:
docs/audit/presentation-polish-t041b-2026-10-29.json.

Private scoring-session discovery is intercepted in the targeted browser to
avoid issuing forecasts or touching private ledgers. All third-party traffic
is blocked. Photos/provider freshness and live forecast quality are not newly
validated. No statistical change, model promotion or deployment. Broader UI/UX
work and T042 remain deferred. Publication of this fix branch is explicitly
authorized by the user; main/dev merges are not authorized.
