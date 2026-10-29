# T033 completed after resume

Resumed by owner; implementation/verification completed. Original stop-state
notes below are retained as history, not active instructions. See
ORIGINAL_UI_PARITY.md, NEXT_BALL_PLATFORM_PLAN.md and SESSION_PROGRESS.md for
current state. New work proceeds on subsequent chained ticket branches; no push,
merge or deployment is authorized.

# T033 handoff ? stopped at owner request

Branch: feat/t033-cricket-workflows, based on T032 c355d9c.
All T033 changes are UNCOMMITTED. No push, merge or deployment occurred.
User explicitly stopped development; do not resume until instructed.

## Completed investigation

Playwright visited8original deployed pages and captured19desktop/mobile
interaction states: comparison player/team choices; profile Overview/Career/
vs Teams/At Venues/Probability/ML; match Overview/Scorecard. Original evidence
is in build/t033-audit/reference-inventory.json and reference-interactions.json,
with screenshots. Reference URL: https://criclytics.aliamirchoudhary.workers.dev/.
Some old figures/attributes are static placeholders; UX restoration must not
restore invented probabilities, stale rankings as current, or false-live labels.

## Work in progress

- Original blue theme and DM Serif Display/Outfit fonts restored locally with OFL
  notices. New cricket-experience.css and experience.js are loaded by19pages.
- Browsable player cards, card/table switch, format/record buttons, selectable
  searchable comparison lists, team mode and observed frequency panels.
- Profile format tabs plus Overview/Career/vs Teams/At Venues/Probability/ML views.
- Match Overview/Scorecard/Probability/ML views.
- Prediction centre discovers local sessions via new guarded GET
  /api/v1/workspaces; no required ID typing. Past issued joint probabilities and
  frozen model comparison report visible. Technical details now collapsed.
- Rankings UI uses actual dataset leaders; obsolete hardcoded ICC ratings are
  replaced by an archive notice and official source link. This is NOT a current
  official ICC feed.
- New optional PLAYER_MEDIA_MANIFEST serves locally prepared, hash-checked JPEG/
  PNG portraits via /api/player-media. Exact unique identities only.36distinct
  provider headshots (161368bytes) live in ignored build/t033-player-media/, not
  public Git assets. Existing two CC portraits remain as fallback. Manifest
  records source and non-commercial editorial scope. CricketData terms explicitly
  forbid hotlinking and instruct image download/own hosting; do not claim CC rights
  or distribute these provider originals as a public dataset.
- Public static/data/model-evidence.json is an extracted frozen evaluation summary,
  NOT weights or a new performance/promotion claim. Learner does not beat stronger
  phase baseline. Prospective cohort remains zero.

## Live-score research and current integration

CricketData official widget page grants free unlimited embedding/no key, but its
sandboxed local widget request returned Invalid referer. Official source page
worked. Do not spoof referrers or bypass provider restrictions. The trial owned
static/widgets/live-scores.html file and its CSP exception were removed.

CricTimes official widget pages explicitly provide free iframe embedding and
color customization for personal/commercial sites:
https://crictimes.org/live-cricket-score-widget
https://crictimes.org/cricket-score-widget-builder
Playwright opened https://widget.crictimes.org/ successfully (200, recent scores,
Recent/Live/Upcoming tabs, no JS errors). Current experience.js now embeds the
canonical cwidget.crictimes.org variant with supported dark color parameters,
ONLY on Load live scores click. Parent CSP allows this one frame origin; app
scripts remain self-only. External provider frame is sandboxed scripts/same-origin
on its DIFFERENT origin; no top navigation or app/private-note access. Close
removes iframe. Need actual in-app test of this final variant. Do not claim a
validated low-latency feed or use widget DOM as model input. No backend API source
allowlist was changed; automatic collectors remain blocked.

## Local preview and verification

Preview server: build/t033-preview/run.py, port5050, PID in its server.pid.
It reuses the existing completed historical replay and ledger without restarting
its producer. Added media manifest config. Original source/history retained.
The RUNNING Python server predates the latest parent CSP change from the failed
CricketData trial to CricTimes; restart only this verified preview process before
final widget verification. JS/CSS/templates are read from current source.

Full89-test suite passed (88pass/one optional skip) after initial backend edits,
before final widget changes. Three new tests in tests/test_cricket_experience.py
passed after fixing a Windows SQLite connection cleanup. Those tests were then
updated for the final external iframe, so rerun them/full suite after resuming.
Changed JS syntax passed. Current Playwright preview screenshot matrix for
home/players/compare/records/rankings/predictions at375/1440 showed no page errors
or overflow before final widget changes. Evidence/screenshots: build/t033-preview/.
One initial full-page capture failed transiently; rerun succeeded. Final complete
95-case responsive audit has NOT been run for T033. No finished audit claim.

## Next steps

1. Finish actual reference inventory (remaining pages/search, team/venue profiles,
   match flows) and write a concise old/new feature parity audit.
2. Restart verified local preview, test actual CricTimes iframe load/tabs/close,
   no request before click, privacy isolation and denied-provider fallback. Parent
   should offer a useful external link if provider unavailable, not hang silently.
3. Audit/fix all new current flows with Playwright: comparison selection/search/
   team switch/same-player prevention/format changes; player card filtering,
   pagination and image failures; all profile tabs; records/rankings; match
   scorecard; prediction session selection/history/expiry; private scouting notes.
4. Review source/date/model labels and final UI. Source session buttons currently
   omit historical match dates; consider adding them. No current live stream was
   established by this work. Official rankings still need an approved fresh source.
5. Consider a bounded photo-gallery filter: optional idea only, not implemented.
6. Add useful verification evidence, run full unit suite, Python compilation,
   JS syntax and19page/5width browser matrix. Update T033, index and progress.
7. Only when actually complete, local commit on THIS new branch is authorized
   using aliamirchoudhary <aliamirchoudhary@gmail.com>. No push/merge/deployment.

No global settings, billing, account creation, credentials, production resources,
original datasets or model artifacts were modified.
