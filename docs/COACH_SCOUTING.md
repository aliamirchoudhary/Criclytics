# Coach preparation and private plans

T029 provides descriptive scouting at `scouting.html`, linked from navigation and
player profiles. It is the19th allowlisted/static page. It requires the opt-in
identity-correct candidate from PLAYER_ID_AGGREGATES.md; name-keyed legacy rows
are never substituted. `/api/v1/scouting` accepts only public player/bowler/format/
opponent/venue selectors. Ambiguous names return409; unknown identities404;
unconfigured identity evidence503. No private notes or source writes are accepted.

Choose a batter by source ID or unique alias, format, optional bowler, and the
opponent/venue source names. Suggestions derive from that player's observed
records. The report includes player-format batting, selected bowler-format bowling,
batting against the selected opponent/venue, recent **all-format** innings,
coverage, dataset/store/report identity and Cricsheet ODC-BY attribution. It does
not infer nationality, complete careers, a matchup advantage or a coaching verdict.
Changing selectors invalidates the previous evidence until refreshed. A different
venue/opponent is a descriptive slice, not a counterfactual probability estimate.

An optional small delivery archive adds batter/bowler and T20I phase counts:

```powershell
build/env312/Scripts/python.exe -m criclytics_app.pipeline.scouting --source build/events-t20-v1.sqlite3 --output build/scouting-delivery-v1.json
```

Set `SCOUTING_SAMPLE` explicitly to the private resulting JSON in a local factory
configuration. Startup binds it to the selected player dataset. The offline
builder reads latest canonical revisions under one SQLite snapshot, caps100matches/
50,000attempts, excludes super overs and writes only a fresh private output. It
records logical source-event and physical source-store hashes, source dates and
unknown publication availability. It does not alter the event store.

The measured local sample is100historical matches,23,104attempts,2016-06-18 through
2018-10-27. It is separate from the6,651-match summary corpus and is not a complete
head-to-head career. Pair/phase rows are **not conditioned on selected opponent or
venue**. Powerplay is overs0..5, middle6..14, death15+ for T20I; other formats have
no inferred T20 phases. Counts distinguish attempts, batter balls (no-balls count,
wides do not), batter runs, striker dismissals and bowler-credited wickets.
Run-outs do not become bowler wickets; non-striker dismissals do not become batter
matchup dismissals. Missing pair/phase rows stay unavailable, never zero risk.

The model is not invoked. Missing weather, pitch tracking, field placements,
mental state and unreviewed incidents remain explicit exclusions. There is no
causal, current-form or pressure effect inferred from source statistics.

Private tactical notes, roster and what-if assumptions live **only in the current
page's memory**. They are not put into URLs, API bodies, cookies, localStorage,
IndexedDB, shared caches, logs or public static artifacts. There are no hosted
accounts or private server persistence, so server auth/CSRF ownership is not
claimed. Public scouting is read-only; the selected scope may appear in ordinary
browser navigation. Never put private information into the public selector fields.

Export private plan explicitly downloads bounded JSON containing selections,
notes and public evidence; anyone holding that file can read it. Export public
evidence excludes all private fields. Refresh/navigation/closing loses notes
without an export. Import is local only, validates exact schema/field/UTF8-byte
limits and keeps existing notes on invalid input. Imported evidence is unverified
until refreshed. Separate tabs have separate memory, not an authenticated
cross-device ownership guarantee. Test restore from a saved file before relying
on it, and keep your own private backup; no free host disk persistence is assumed.

Evidence: `audit/scouting-sample-2026-10-28.json`,
`audit/coach-workflow-2026-10-28.json`, and the separate19page/five-width UI audit.
Actual local data browser tasks cover preparation/filter, hostile-text private
export/import, no note network requests, public export exclusion, reload loss,
separate-tab isolation and invalid-import preservation. These are agent task
simulations. **Real coach feedback remains pending**, and T031 must not call this
a measured coach pilot. No external feed, credential, paid service, remote write,
model promotion or deployment occurred.

Rollback: clear optional `SCOUTING_SAMPLE` to remove delivery evidence, or clear
`IDENTITY_PLAYER_STORE` to make scouting unavailable; restart and retain artifacts
for audit. Private exported files belong to the operator and are never migrated
or deleted by the application.
