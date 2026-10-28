# Identity-based historical player summaries

T017A replaces aggregation by ambiguous display labels with aggregation by the
Cricsheet player identifier from each match. Names are substituted before the
validated innings scorer runs. Different people with the same label remain
separate; different labels carrying one identifier combine once. Missing source
IDs retain the match-scoped provisional identity used by T017. Super overs remain
separate from regulation summaries, as in SCORING_CONTRACT.md.

The candidate includes rostered players with no scored innings and players with
bowling records but no batting innings. `stats_available` distinguishes them.
Batting yearly/opponent/venue tables reconcile to player-format innings and runs.
Bowling summaries reconcile to credited wickets and scored bowling innings.
These tables describe the available men's international subset, not full careers.
Opponent and venue breakdowns are batting summaries; venue names are source
labels, not an assertion that all renamed venues have been combined.

Generate a fresh candidate, preserving source and existing processed artifacts:

```powershell
build/env312/Scripts/python.exe -m criclytics_app.pipeline.player_id_stats --parent build/data-v3-manifest-final --registry build/identities-v1-final.json --output build/player-ids-v1-final
build/env312/Scripts/python.exe -m tools.check_player_id_stats --candidate build/player-ids-v1-final
```

`manifest.json` binds the parent dataset identity, exact identity-registry hash,
source-count reconciliation, code hashes and SQLite checksum. Parent manifest
validation and every selected raw-file hash precede aggregation. A failed rebuild
has no manifest and cannot be selected. Use a fresh output path for a retry.
No candidate is automatically promoted. SQLite is private, immutable after
publication and opened in read-only mode by the application. Queries decode only
bounded selected profiles, not a process-wide copy of every detailed profile.

To review locally, explicitly select the matching processed dataset,
`IDENTITY_REGISTRY` and `IDENTITY_PLAYER_STORE`. Factory initialization rejects
mismatched datasets/registry/database checksums. These local artifact hashes are
integrity checks against operator-selected files, not signatures for accepting
untrusted uploaded databases. No upload endpoint exists. Keep candidates outside
the public deployment output. Roll back by clearing `IDENTITY_PLAYER_STORE` and
restarting, retaining candidates for review. That restores legacy statistics and
their documented limitations; it does not make them identity-correct.

With the option enabled, players/profile/comparison/search/stat-ranking/record
and venue-player leaderboards use ID-based summaries. Unique names still resolve;
ambiguous aliases return409 even if one candidate lacks scored innings. The player
directory searches all registered aliases and provides ID links for disambiguation.
Curated name-keyed biographies/countries are not joined onto new profiles.
`country` is null; `observed_teams` includes attributed membership dates/counts.
The existing `country` query parameter filters observed team memberships on the
candidate; the UI explains this compatibility contract. A player's announced
role, nationality and complete career are not inferred from these observations.

Venue leaderboards combine observed formats, explicitly labelled in the UI, and
keep the existing minimum-run/wicket inclusion thresholds. IDs now separate
same-name players. They are descriptive records, not pitch-context evidence.
Display names remain source labels and can therefore match across two profiles;
identity links and membership dates distinguish them. Scorecards and external
ranking snapshots retain their original source names and may lead to an explicit
ambiguity choice rather than inventing a source-ID join.

Full candidate and browser evidence is recorded in
`audit/player-id-aggregates-2026-10-28.json`. Provider feeds, prediction promotion,
hosted release and private coach workflows are separate tickets.
