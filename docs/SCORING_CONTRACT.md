# Scoring contract v2

This is an explicitly changed statistical contract. The versioned rebuild is a
candidate, not an automatic replacement of data/processed. Current historical
files and their hashes are preserved. Scope is the local male international
subset, not full careers or all cricket. Data attribution: Cricsheet,
https://cricsheet.org/; JSON data under Open Data Commons Attribution 1.0,
https://opendatacommons.org/licenses/by/1-0/. Source notices remain in data/raw.
Licensing source: https://cricsheet.org/licensing/ (checked 2026-10-28).

Implementation uses match file + innings index + player + over identities.
Regulation innings contribute independently to milestones, highest, dismissals,
not-outs, yearly form, bowling best figures and five-wicket hauls. Super overs
remain in detailed scorecards but are excluded from regulation career summaries.
Recent form is sorted by match date/file/innings across formats; each Test innings
is separate. These are observed innings, not inferred complete career coverage.

Delivered no-balls count towards batter balls faced but not legal bowling balls;
wides count towards neither. Byes and leg-byes still count as faced/legal when
not combined with a no-ball. Bowler runs comprise batter runs plus wides and
no-balls, excluding byes, leg-byes and penalties. Boundary counts respect the
Cricsheet non_boundary flag. Innings penalties before/after deliveries enter team
totals without assigning them to a batter/bowler. These conventions are supported
by New Zealand Cricket's Scorer Companion (2016), pages 6, 11, 23:
https://www.nzc.nz/media/12873/scorer-companion-final-2016.pdf.

Only bowled, caught, caught-and-bowled, lbw, stumped and hit-wicket dismissals credit
the bowler. Non-striker dismissals update the actual player_out. Retired hurt/not
out do not count as a team wicket or batting dismissal; retired out/timed out and
other non-bowler dismissals do. Reappearance after retirement uses the same
innings identity. A completed single-bowler over with no runs conceded is a maiden;
a partial over is not, including a zero-run final fragment. Declared miscounted
overs use the source's official delivered-ball count. Mixed-bowler overs do not
generate an invented maiden. Zero dismissals gives a null batting/bowling average.

Draw/tie/no-result are distinct outcomes. Test innings are numbered, not treated
as repeated limited-over chases. Format-specific limited-over chase samples are
provided; no all-format chase likelihood is published. T20 phase summaries use
conventional over bands 0-5,6-14,15+ only for observed phases, including zero-run
phases. They are descriptive bands, not assertions of official powerplay rules
in shortened games. No phases are inferred for an unobserved innings segment.

Schema reference (including super_over, penalty_runs, miscounted_overs and
retirement representation): https://cricsheet.org/format/json/.
MCC scoring/extra laws:
https://lawsofcricket.lords.org/laws-of-cricket/the-over-scoring-runs-dead-ball-and-extras/scoring-runs
and https://lawsofcricket.lords.org/laws-of-cricket/the-over-scoring-runs-dead-ball-and-extras/no-ball.
Scoring consumes recorded events; it does not infer absent dead-ball/dismissal
observations or claim to adjudicate laws from video.

Rebuild: `python -m criclytics_app.pipeline.cricsheet --output build/data-v2-full`.
Output must be fresh and outside raw sources. The manifest records source hashes,
output hashes, schema and original artifact hashes. Rejected inputs have a ledger;
unexpected aggregation failure aborts the candidate. A directory without a final
manifest is incomplete. No serving path switches automatically. Rollback keeps
the old directory and selects a reviewed complete artifact, without deleting data.
