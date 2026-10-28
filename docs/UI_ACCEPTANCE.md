# T011 UI acceptance ? 2026-10-28

The 17 public URLs now use one data-driven renderer and compact page scaffolds.
The navy/blue palette and public URLs are retained. Original markup is preserved
under history/ui-pre-t011; it is excluded from public build output. Unsupported
Follow/demo actions were removed. Descriptive statistics retain their source
coverage warning; forecasts remain unavailable. No data candidate was promoted.

| Page | Available actions and states |
|---|---|
| index | Recent/results and cached upcoming links; provenance and unavailable forecasts |
| matches | Status, format, team and order filters; bounded server pagination; detail links |
| players | Name, country, format, role and sort filters; pagination; profile links |
| teams | Name/format filtering and team profile links |
| venues | Name/format filtering and venue profile links |
| player-profile | Recorded entity lookup; format tabs; batting/bowling, yearly/opposition/venue and recent innings tables |
| team-profile | Recorded entity lookup; format tabs; opponent/venue records; denied crest fallback |
| venue-profile | Format tabs, recorded venue figures and leading batters/bowlers |
| match-detail | Required ID, cached status, innings tabs, batting/bowling and fall of wickets |
| match-upcoming | Required ID, cached fixture provenance and unavailable forecasts |
| rankings | Category/format controls; source dates and stale/fallback labels |
| records | Format/category controls and observed records |
| search | Labelled query form; bounded player/team/venue/match results and entity links |
| compare | Player/team selection, exact recorded names and format; descriptive comparison only |
| about | Coverage and product limits; shared navigation/search |
| data-sources | Source attribution/licensing link and cache limitations |
| disclaimer | Historical-data and prediction limitations; shared navigation/search |

Every page has a skip link, labelled search/navigation, one main heading and
keyboard focus styles. Native mobile navigation, labelled forms, roving keyboard
tabs and scrollable labelled tables support narrow screens. Loading, empty,
missing parameter, unknown entity and request failure have explicit states.
Missing values remain unavailable; recorded zero stays zero. API failures never
retain demo metrics. Search match limits and null-safe player sorting were also
fixed with a regression test.

## Verification

- `python -m unittest discover -s tests -v`: 41 tests, 40 passed, one optional skip.
- Python compilation, `node --check criclytics_app/static/js/application.js`, and Git whitespace checks passed.
- `python -m tools.check_application_ui`: 17 pages at320/375/768/1024/1440 (85 cases), zero page errors, unnamed visible controls, lingering loading states or document overflow. Denied images, keyboard tabs, missing/unknown entities, empty filters and API503 states passed.
- `python -m tools.check_application_interactions`: real pagination/team comparison, malicious long names at allfive widths, zero/null rendering and reduced motion passed. Four selected authored contrast pairs exceeded4.5:1; an ARIA tree was captured.

Commands used the project-local Python3.12 environment and free local Chrome,
with external images/fonts denied and the unpromoted schema2.0.1 candidate.
Evidence: audit/application-ui-2026-10-28.json,
audit/application-interactions-2026-10-28.json and
 audit/application-aria-2026-10-28.txt. Screenshots are local ignored build artifacts.
These checks supersede old selector-dependent page audit helpers for the replaced
templates; legacy helpers are not evidence for this UI. Tool consolidation remains
T012. No manual screen-reader speech, exhaustive contrast/WCAG certification,
cross-browser acceptance or hosted latency verification is claimed.

## Review and rollback

Review/integration remains pending. No deployment or remote Git mutation occurred.
Default serving still selects existing processed data, whose historical figures
remain under review. The new candidate is used only for this local acceptance run.
Rollback can restore the archived templates and remove the new renderer/styles
through a reviewed follow-up change; API bounded-search/null-sort fixes are
independent. Runtime configuration/cache consolidation remains T012.

Execution stops after T011 at the user's request. No T012 work was started.
