# Ingestion and golden contracts (T010)

pipeline/schema.py validates the source boundary before aggregation. Supported
Cricsheet JSON versions are1.0.0/1.1.0/1.2.0/1.3.0, current international Test/ODI/
T20 formats and six-ball overs. Unsupported versions/over lengths are rejected
explicitly. Structural unknown fields in match/meta/info/innings/over/delivery/
runs/extras/wickets and consumed penalty/miscount/target objects are rejected.
Scoring integers reject booleans, negatives and arbitrary numeric strings;
delivery totals/extras must conserve runs. Teams, dates, player lists, innings
flags and duplicate dismissals/overs are checked. Some recognized non-scoring
metadata (registry, events, replacements, reviews) remains opaque and is not used
as a model feature. This validator does not adjudicate every possible legal match
state; the canonical replay contract is T018.

SchemaError carries a stable code and location, without echoing source values.
Rebuilds quarantine malformed inputs in the report before changing accumulators.
Unexpected aggregation errors abort an incomplete candidate. Only the narrow
legacy miscounted-over digit-string field is normalized, in memory with an audit
ledger. Cricsheet penalty keys are pre/post, validated against the source schema
https://cricsheet.org/format/json/. The initial full-corpus schema audit found80
files requiring that normalization and8 penalty-key mismatches in our draft
validator/scorer. Both are covered by regression tests and v2.0.1 correction;
unknown fields are not broadly discarded to make the audit pass.

Fictional golden data and hand explanations: tests/fixtures/cricket_golden.json
and tests/fixtures/README.md. Their CC0 dedication covers only authored synthetic
data. The real Cricsheet data remains ODC-By1.0 with its original notices. Routine
unittests need neither ignored source artifacts nor provider accounts. Equivalent
rebuilds are compared as parsed JSON (not OS newline bytes) including manifests.
A corrupt input must produce a rejection code; an existing output directory must
be refused. Golden API checks cover players, match lists/details, H2H and venue
nesting, and include abandoned matches and super-over separation.

`/api/h2h?team_a=...&team_b=...&format=...` returns one record oriented to the
requested team order, with distinct draws/ties/no-results. Without format it
returns a format-keyed map. T20 is normalized to T20I; match callers normalize
provider spellings, use the match format and skip unknown formats. Historical
H2H fingerprint equality was retired in T004 and is replaced by semantic tests.

`python -m tools.final_verification` now checks response status and JSON contracts
in-process offline, or against an explicitly supplied --base-url. It returns1 on
any failure and does not claim model validity, data completeness or production
readiness. A failed localhost connection was verified to return nonzero. Imports
are side-effect free. Full read-only source validation is optional:
`python -m tools.validate_corpus --raw-dir data/raw --report build/schema-report.json`.
