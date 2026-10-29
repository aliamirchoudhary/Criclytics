# Real rankings and retained backup (T036)

The official ICC pages were visited through ordinary Chrome without login,
challenge bypass, forged referrers, hidden endpoint discovery or retries. Two
personal local extracts were retained: men's T20I batting20rows and teams100rows,
both explicitly dated2026-10-27 by the page. Source HTML, derived snapshots and
screenshots remain ignored under build/. No ranking values are committed as a
new fabricated/current dataset.

Sources: [batting](https://www.icc-cricket.com/rankings/batting/mens/t20i),
[teams](https://www.icc-cricket.com/rankings/team-rankings/mens/t20i),
[terms](https://www.icc-cricket.com/news/icc-website-terms-of-use),
[robots](https://www.icc-cricket.com/robots.txt), checked2026-10-29. Robots allows
the ranking paths but does not grant reuse rights. Terms permit personal extracts
subject to law, reserve content rights and require a licence for commercial use.
This is no established public redistribution basis. No outreach/licence purchase.

The new importer is OFFLINE; it never requests a provider. Backend network
collectors remain denied by the source-policy allowlist. No scheduled scraper is
enabled. Import a locally retained rendered HTML page with its actual observation
timestamp (do not substitute today's date for the official ranking date):

```powershell
python -m criclytics_app.integrations.ranking_snapshots --html build/personal-ranking.html --store build/rankings.sqlite3 --category batting --format T20I --observed-at 2026-10-29T00:00:00+00:00
```

Supported parser categories: batting, bowling, allrounder, teams; formatsTest/ODI/
T20I, men only. Two real T20I table shapes were checked; other tables require a
real import before claiming coverage. Scope, official date, exact columns,
bounded unique identities, rank/tie/rating ordering, row count and team totals
are validated. Layout drift fails closed. No fuzzy player-identity linking.

SQLite transaction publishes a current snapshot and retained prior valid slot
per category/format. The first valid observation seeds both slots. Hashes cover
the derived payload; raw rendered HTML is retained unmodified in each slot.
Unchanged HTML does not advance observation time. Older/malformed imports leave
last good data intact. A corrupt current payload falls back to its retained slot
with backup/stale status visible. This is not recovery from total database/disk
loss; normal private file backups are still necessary for durable hosting.

Set RANKING_SNAPSHOT_STORE to the private SQLite file for LOCAL personal preview.
Both socket peer and Host must be loopback, same-origin, not cross-site. Forwarded
headers never grant access. Public callers receive empty unavailable data; there
is no config flag granting public reuse. The API is no-store, exposes no paths or
raw HTML. Official effective date and original observation date remain separate.

The rankings screen offers dataset batting/bowling leaders and ICC snapshots
with category buttons, dates, source link and unavailable-category handling.
The old hardcoded April data remains only as a historical artifact/helper; the
public /api/icc-rankings route no longer serves it as a fallback. Contract change:
unconfigured/no approved public snapshot returns available:false,rankings:[];
callers must use that availability field. Both API and UI were migrated together.

Tests cover failed refresh preservation, unchanged observation, corruption backup,
repair without losing backup, ties/zero rating/team totals and remote/Host/Origin
privacy gates. Actual375/1440UI checks cover dated20/100row views and unavailable
bowling; see docs/audit/rankings-ui-t036-2026-10-29.json. Wider restored cricket
workflows also pass. Public automated updates remain blocked on a $0 rights basis.
