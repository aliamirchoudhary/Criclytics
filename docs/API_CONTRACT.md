# API request and error contract

T004 validates inputs before loading datasets or invoking providers. A missing
dataset must not mask an invalid request. Limits are integers 1–500, offset is
0–100000, page is 1–10000; text is at most 200 characters with no controls or
duplicate query keys. Formats and prediction metrics are explicit enums.
Team-match POST requires an application/json object with different nonempty
string teams, valid format and optional bounded string venue. Body cap is 64 KiB.

Success representations stay unchanged until the pagination/model tickets. Error
responses have `error` (safe text), `code` and `request_id`; X-Request-ID matches
the request. Invalid request=400, unknown route/entity=404, body too large=413,
wrong media=415, missing required artifact/service=503 and unexpected failure=500.
Optional context absence is no longer a successful 200 with an error-shaped body.
The shared frontend fetch helper already handles non-success statuses as an
unavailable panel; callers must not convert this to invented statistical values.

Internal exception contents and provider URL query strings never belong in
response errors. Existing error-shaped legacy route returns are normalized at
the API boundary while their handlers are extracted into services. Logs report
exception type/request ID, not exception messages. Original response fingerprints
apply to unchanged successes, not the deliberately corrected error contract.

## T005 fixture listings

`GET /api/matches` returns compact `data` and `pagination` (`total`, `limit`,
`offset`, `has_more`). Default limit 20; maximum 500. Filters: status
(all/upcoming/live/completed), exact team (documented short aliases), exact venue,
date prefix and format (T20/T20I equivalent). Sort: newest/oldest/format with ID
as deterministic tie breaker. `competition=ipl` requires explicit series evidence.
No fuzzy provider identity merges. Pagination is stable for a fixed source snapshot;
refreshing sources can change offsets. Clients should reset pagination after filters.
Scorecard details remain exclusively on `/api/matches/<id>` and `/score`.
Search already projects bounded match fields; it does not return scorecards.

T004 soft-miss H2H errors and T005 full-corpus listing fingerprints are explicitly
retired from the opt-in legacy equality test; focused error/list/detail contracts
replace them. Historical statistical fingerprints are otherwise retained until
T008/T009 deliberately change their contracts.
