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
