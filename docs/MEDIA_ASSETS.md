# Public cricket media

T032 restores visual media with local assets. No image proxy, provider key,
external image request, paid service or runtime collector is required.

## Flags

The SVGs in `criclytics_app/static/images/flags/` are copied unchanged from
[flag-icons v7.5.0](https://github.com/lipis/flag-icons/tree/v7.5.0/flags/4x3).
Copyright Panayiotis Lipiridis and contributors; the full MIT notice ships in
`flags/LICENSE.txt`. Scotland uses `gb-sct`, England uses `gb-eng`; Seychelles uses
`sc`. Composite/regional cricket teams (West Indies, Asia XI, Africa XI, ICC World
XI) use letter crests, not a substituted national flag. Player-team flags mean
observed memberships, never inferred nationality.

## Portraits

| Player / Cricsheet identity | Author | Source / license |
|---|---|---|
| Virat Kohli / ba607b88 | Anand Anil | [Wikimedia file](https://commons.wikimedia.org/wiki/File:Virat_Kohli_portrait.jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Babar Azam / 8a75e999 | BBC Urdu | [Wikimedia file](https://commons.wikimedia.org/wiki/File:Babar_Azam_in_2020.png), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) |

Original image bytes are retained, with SHA-256 hashes in the bundled
`images/players/credits.json`. CSS uses a display crop; original licenses remain
attached to these assets, including share-alike on the Kohli photograph. Source,
author and license links appear next to the featured/profile images and on the
Data sources page. Editorial identification only; no player endorsement claimed.

The curated photo catalog currently covers **two players**, not the full player
database. It is bound to exact stable IDs, never a fuzzy or shared name. Other
players have labelled initials; image errors preserve initials without breaking
the page. Existing third-party `players_meta.json` URLs are retained as original
data, but are not blindly rendered or downloaded. A further Wikimedia portrait
download returned HTTP429 and was stopped; no retries or access-control bypass.

To add a portrait: verify the actual file's author/license, save its allowed image
locally, record the source/license/hash, verify its stable player ID, extend
`media.js`, and add its visible attribution. Do not use AI-generated likenesses as
real player photographs or mark unknown rights as public domain.
