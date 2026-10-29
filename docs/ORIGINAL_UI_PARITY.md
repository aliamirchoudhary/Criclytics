# Original-site interaction audit and T033 restoration

Reference: https://criclytics.aliamirchoudhary.workers.dev/, inspected with actual
Playwright/Chrome navigation and clicks. Evidence: audit/original-reference-t033-
2026-10-29.json; full observed text/screenshots remain in build/t033-audit/.

Eight original main pages plus seven additional page types were visited; player
and match profiles were exercised separately. Nineteen desktop/mobile interaction
states include player/team selection and the six player profile views. The old
match ML tab locator timed out in one case; not all original controls are certified
functional. Reference pages mix fetched data with static/demo content.

| Area | Original experience | T033 implementation / remaining limit |
|---|---|---|
| Home | Blue serif identity, quick access, live ticker, player cards | Original local fonts/blue theme, quick access, score centre, player cards, prediction-first entry; external widget opened on request |
| Players | Grid, format chips, search, role/team filters | Actual-data24-card pages, format/role/view buttons, search, pagination, compare/scout actions; no invented trending/roles |
| Photos | Mixed provider/Wikimedia hotlinks, many failures |36unique local provider headshots plus CC fallback; exact ID binding; provider originals excluded from public Git bundle |
| Compare | Two searchable selectable lists, team mode, format buttons | Both lists restored with actual stable IDs, bounded search/paging, selected previews, team mode, automatic results and same-identity protection |
| Player profile | Overview, career, opposition, venues, probability, ML tabs | All six visible views restored; real innings frequencies and frozen model evidence clearly distinguished from forecasts |
| Match centre | Live/upcoming/results and formats | Status/format buttons, score snapshots with source status, free external score panel; no current timeliness guarantee |
| Match detail | Overview, scorecard, insights | Overview/Scorecard/Probability/ML tabs; model entry tied to scoring-session availability |
| Records | Format/category tabs and leader tables | Tabs/buttons, correctly labelled actual available-match records; no hardcoded career-record hero or mismatched metric columns |
| Rankings | Old hardcoded ratings presented as official/current | Actual dataset leaders by default; official source link and archive notice; fresh official import handled in T036 |
| Teams/venues | Browsable records and profiles | Existing actual-data navigation and safe profiles retained; broader card enrichment remains possible |
| Search/info | Cross-entity search, source/disclaimer pages | URLs retained, image/identity enhancements, media attribution and coverage |
| Prediction centre | Main distinctive feature was difficult to discover | Primary home/nav entry, selectable local sessions, past/current joint probabilities, explicit source/mode/expiry, model comparison evidence |

## Live display decision

The CricketData script widget was tested and returned Invalid referer on the local
sandbox origin; its official source page worked. No referrer spoofing or workaround
was attempted. The trial integration was removed.

The final source is the [documented CricTimes iframe](https://crictimes.org/live-cricket-score-widget),
with [documented color customization and free personal/commercial embedding](https://crictimes.org/cricket-score-widget-builder).
The provider document remains on its own origin, inside a sandbox; scripts cannot
read the application/private plans. No API key/account or billing is configured.
Parent scripts remain self-only. Open/close and real provider rendering are tested;
its lag/coverage are unvalidated, and its DOM is NEVER an ML input or scraped feed.

## Verification

T033 final evidence:95page/width cases plus4failure/keyboard interactions;
375/1440workflow checks including selections, six profile views, records,
leaderboards, session discovery/issued probability display, real widget load/close
and blocked parent access.92unit tests:91pass/one optional legacy-data skip.
Compilation, JS syntax and static-build checks accompany the ticket. Chrome-only
local evidence is not real coach acceptance, cross-browser certification, hosted
capacity or predictive promotion. New broader work: NEXT_BALL_PLATFORM_PLAN.md.
