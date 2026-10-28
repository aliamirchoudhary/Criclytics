# T029: Build coach scouting scenarios and private workflows

- Status: Implemented locally; coach review pending
- Priority: P2
- Depends on: T010,T012,T017,T017A,T020,T023
- Branch: feat/t029-build-coach-scouting-scenarios-and-private-workflows
- Base: latest dev

## Problem

Generic profiles lack actionable preparation reports, transparent scenario assumptions and safe private notes.

## Scope

Implement focused opponent/bowler scouting with matchup/venue/phase/form evidence, sample sizes and attributed export. Add explicit what-if assumptions without causal claims. Private notes/rosters require tested ownership/session/CSRF and durable free storage; use local-only export if persistence cannot be guaranteed.

## Acceptance criteria

- [x] Coach can prepare a plan and trace every statistic to source/cutoff/coverage
- [x] Scenario changes expose assumptions/uncertainty rather than proven causal advantage
- [x] Private data never leaks via public static/API; cross-user isolation tested if accounts exist
- [ ] Real coach feedback and ephemeral-storage loss/local-export behavior are documented

## Validation

Coach task walkthroughs, export/attribution tests, auth/CSRF/ownership tests when applicable and restore/export checks.

## Handoff

Read AGENTS.md and the matching findings in docs/AUDIT.md. Budget: $0, no card or paid fallback. Preserve unrelated changes/data. Record changed contracts, checks/results, risks and rollback below. Mark Done only after review/integration.

## Implementation evidence

Local implementation and simulated tasks verified. Real coach feedback remains pending; the final acceptance item is deliberately open.

T017A is required for identity-correct global player summaries; do not present
legacy collided-name totals as validated scouting careers.

### Session update 2026-10-28T17:21:51+00:00

Chained from T028 381c27d. Source-ID-only scouting evidence, optional bounded delivery archive, explicit descriptive assumptions and browser-memory private plans with local export/import; no hosted private storage.

### Session update 2026-10-28T17:30:38+00:00

Source-ID-only public scouting report and19thpage; full summary vs separate100match/23104attempt archive scope explicit;3498pair/708phase rows reconcile, stable source hashes. Opponent/venue/bowler evidence and sample counts; missing context unavailable/no causal scenario or forecast. Private notes/roster/assumptions stay in page memory with bounded local JSON export/import, no server persistence/URL/transmission/autosave. Browser375/1440 actual-data preparation/filter, safe hostile text, private restore/public export exclusion, reload loss/tab isolation/invalid import preservation pass.19pages*5widths=95cases+4interactions pass.86tests85pass/one optional skip; latest focused2tests pass; compilation/JS syntax pass. Docs COACH_SCOUTING.md and audit/coach-workflow, scouting-sample, application-ui-t029 reports. Real coach feedback is null/pending, not substituted with agent simulation. No hosted accounts/auth guarantee, paid service, deployment or push.
