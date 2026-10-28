# Weather context decision ? 2026-10-28

Weather is excluded from modelv1. No provider request, paid service or credit-card
activation occurred. A location/time join is not invented: the selected historical
sample lacks exact ball UTC times and an attributed as-issued weather archive.
All23,104 attempts therefore have unknown eligible weather. An ablation claiming
benefit would be invalid; benefit/cost metrics remain null, inclusion=false and
external call cost0. The existing held-out baseline is unchanged. Future data can
be considered only in a newly preregistered chronological experiment.

Source review:

- [Open-Meteo terms](https://open-meteo.com/en/terms) and [pricing](https://open-meteo.com/en/pricing) restrict the free service to non-commercial use despite CC-BY data. A professional coaching platform's intended deployment is not automatically eligible. No commercial subscription is allowed by this project's budget.
- [Historical forecast documentation](https://open-meteo.com/en/docs/historical-forecast-api) starts around2022 and stitches short-run sections; this does not supply full as-issued forecast runs for the2016?2018 sample. Reanalysis is not a forecast that was available before a delivery.
- [MET Norway licence](https://api.met.no/doc/License) permits attributed weather reuse underCC-BY4.0/NLOD2.0. Its [terms](https://api.met.no/doc/TermsOfService) require identifiable app/contact, careful caching and bounded aggregate traffic; [getting started](https://api.met.no/doc/GettingStarted) explains Expires/conditionalGET and coordinate precision. Locationforecast2.0 is a future optional candidate, not a proved historical join or a new cricket feed. No source is enabled by this ticket.

If later activated after source/contact/venue review, budget one shared weather
request per venue per hour, at most24per venue/day and96application requests/day,
never before Expires; use conditionalGET, coordinate precision at most4decimals,
a descriptive contact User-Agent, jitter and a kill switch on errors/limits. These
are application ceilings, not a claim the provider guarantees this quota or an SLA.
No per-visitor polling, auto-upgrade or metered fallback. Existing source allowlist
remains empty; do not silently enable weather through cricket-provider flags.

`services.weather` supplies pure local schema/UTC/cache/eligibility helpers.
Venue locations require a stable ID, explicit coordinates/timezone, source and
known-at timestamp. No coordinates or timezone are guessed from a display name.
The current Cricsheet venue CSV has no coordinate columns; actual mappings remain
unavailable until separately reviewed. Fixtures use explicitly fictional locations.
DST ambiguous times require fold; nonexistent local times fail. Weather records
retain forecast issue, validity interval, observed time, resolution, source/licence
and per-field missingness. UTC-aware issue/observation/location knowledge must be
at or before cutoff; validity must contain it. Reanalysis is excluded, and unknown
cutoff/location/fields degrade to null. A local128entry cache bounds memory without
claiming durable raw-observation retention. Unit tests cover late issue/retrieval,
DST, cache bounds, zero rain versus unknown wind, invalid ranges and network gates.

Heat, humidity, wind and rain are physical measurements/forecasts, not evidence
that a player feels pressure, a ball must bounce low, dew is present or catches
will be dropped. No pitch-bounce/psychological feature is inferred. Source data
rights, usage conditions and archive coverage must be rechecked before collection.
