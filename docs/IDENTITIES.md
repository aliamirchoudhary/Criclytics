# Stable cricket identities

`python -m criclytics_app.pipeline.identities --raw-dir <raw> --dataset <validated-dataset> --register-dir <licensed-register-csvs> --output <fresh-private-json>`

This explicit offline command verifies every selected accepted input hash against
the dataset manifest. The registry binds to that dataset_id and records hashes
of People/names/Venues/venue_names CSVs. It never discovers provider IDs by scraping.
[Cricsheet Register](https://cricsheet.org/register/) and its separate metadata
licence were reviewed under T015. Source CSVs stay in ignored local build output.

People use `player:cricsheet:<source-id>`, independent of display names. Missing
source IDs create match-scoped provisional identities rather than merging names.
Teams use a deterministic exact-name/gender/team-type namespace; membership date
ranges are observed team appearances, not nationality or continuous contracts.
Venues use an unambiguous official register alias when available, otherwise a
provisional exact venue/city namespace. Provisional identities can require a
future reviewed migration; no fuzzy match or silent destructive rename occurs.
Match IDs preserve `match:cricsheet:<file-id>`; duplicate source IDs fail the build.

Casefolded aliases map to sets. Same-name people and venue aliases can therefore
remain ambiguous;409 requires a stable ID rather than choosing the first record.
Provider person/venue IDs are imported only from the explicit licensed register;
colliding provider identifiers remain unresolved. Source IDs do not license any
provider content. Unknown match-provider IDs remain distinct until reviewed_link
records exact source/target IDs plus evidence and reviewer. Conflicting links fail.
Name/date similarity alone is never sufficient to merge a match.

Set IDENTITY_REGISTRY to the generated private file with the corresponding
PROCESSED_DIR or DATASET_STORE. Startup refuses dataset mismatch. It is opt-in;
legacy/default datasets without a registry retain names and no fabricated IDs.
`/api/identities/<player|team|venue|match>/<id-or-name>` returns identity metadata.
Existing player/team/venue URLs accept stable IDs or unambiguous aliases and add
identity_id; player list and reconciled match summaries also expose it when known.
Recorded source-name URLs continue to select their exact historical label.
A stable ID spanning multiple source labels does not silently combine precomputed
name aggregates: that profile returns409; callers can inspect identity metadata
and select a specific recorded source label. Identity-aware event aggregation is
a separate migration. No statistics are invented or added across overlapping tables.

Venue substring-first lookup has been retired: normalized exact matches must be
unique, and official aliases require the registry. This prevents one short venue
query from picking an unrelated first ground. Public .html URLs are unchanged.
When a reviewed provider/history match link exists, listing retains the completed
historical record and both source references. Unreviewed IDs keep separate rows.

Portable tests cover two people with the same name, rename aliases, observed team
changes, official venue aliases, exact reviewed duplicate reconciliation,
conflicting links, unreviewed lookalikes, stable-ID/name profile compatibility and
mismatched dataset rejection. Real cached provider match comparisons are reported
separately; absence of a proved overlap is not evidence of a confirmed real join.
Raw artifacts and default serving configuration are preserved. Roll back by
unsetting the optional identity registry and restarting; retain old registry
versions and hashes for audit rather than rewriting/deleting source history.

The full scan found5,125 rostered player IDs and5,090 raw roster labels, with68
colliding source labels (111 total alias collisions). The4,834 aggregated labels
count batting/bowling observations and are not the same coverage unit. These
collisions establish a real remaining defect in name-keyed historical aggregates;
do not claim their totals as validated identity careers. Source-ID delivery work
uses the raw registry rather than those combined summaries.25 old cached provider
rows have no date overlap with the historical corpus, so no real cross-provider
match link was asserted. The complete evidence includes register/output hashes.
