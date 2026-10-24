# Criclytics UI Audit Tracker

## Current Goal
Audit and fix UI issues across the deployed web app before starting ML work.

## Current Status
- App launch was attempted from `app.py`.
- Shared responsive CSS was hardened for navbar and filter controls.
- Home page placeholder player names were replaced with real names.
- Venues page got a structural cleanup for the sticky filter bar and duplicate venue container id.
- Browser-tool inspection is still limited to file URLs because the local Flask server is not currently reachable from the browser tool.
- A broader pass has started on static card templates and shared responsive card/grid behavior.
- Player, team, and rankings placeholder names were partially cleaned in the visible card templates.
- `player-profile.html` placeholder hero/bio labels were converted to neutral loading text, and the similar-players panel now uses a plain loading fallback instead of a fake player card.
- `search.html` empty-state chips now point to real example queries, and the search hero received a small mobile spacing tweak.

## What Was Fixed
- Home trending player cards now show:
  - Virat Kohli
  - Babar Azam
  - Jasprit Bumrah
- Shared navbar is now less likely to overflow on small screens.
- Venues sticky filter bar now has explicit layout styles.
- Duplicate `venueGroups` id on `venues.html` was reduced to a single active container.
- Venues sticky controls now wrap/scroll cleanly on narrow screens.
- Grid/card containers now have `min-width: 0` guards and collapse more cleanly on small screens.
- Visible placeholder names were replaced in player, team, and rankings cards.

## What Still Needs Review
- Other pages with obvious placeholder text or demo content, especially compare and any secondary sidebar/demo lists.
- `match-detail.html`, `match-upcoming.html`, and `matches.html` still need a quick responsive/content spot-check.
- Mobile layout issues on pages beyond home and venues.
- Any page-specific overflow, clipped controls, or misaligned chips/tabs.
- App runtime access through browser tooling still needs confirmation.

## Next Checks
- Verify `players.html`, `team-profile.html`, `player-profile.html`, `rankings.html`, `compare.html`, `match-detail.html`, `match-upcoming.html`, and `matches.html` for obvious placeholder UI.
- Confirm responsive behavior for tabs, cards, and sticky controls on small screens.
- Re-run the app when the local server is reachable from the browser tool.

## Notes
- File should be updated after each meaningful UI pass so the work can be resumed easily.
- This tracker is the handoff anchor for the current UI cleanup effort.
