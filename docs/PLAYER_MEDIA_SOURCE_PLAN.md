# Better player imagery: source and quality plan

T044 implements this after canonical identity/lineage work. Source discovery does
not authorize every image or activate a collector. The existing local provider
portraits remain personal-scope; two bundled CC images retain their credits.

| Source | Use | Conditions |
|---|---|---|
| Wikimedia Commons | Primary reusable actual-player photos; local responsive crops | Verify each file's licence, author, source and portrait identity; include credit/licence and change notice; review personality/trademark limits |
| Wikidata | Identity mapping and image references | Structured data CC0 does not make a linked image CC0; image licence is separate |
| Openverse | Discover openly licensed candidates from multiple providers | Search metadata is a lead, not permission; revisit original file, verify current licence/author and exact player |
| Flickr photographs | Additional CC/PD photographs, preferably ones already reviewed in Commons | Do not scrape all Flickr images or assume sports photos are free; original per-file rights must be verified; direct API/access limits need review |
| Player/club/photographer contributions | Consistent headshots with explicit documented reuse permission | Obtain identity/rights evidence before publishing; no unsolicited outreach from the agent |
| Existing CricketData portraits | Retained local personal preview | No automatic public promotion, hotlinking or assumption of sublicensing permission |

Candidate process: exact player ID -> reviewed source identity -> image metadata ->
licence allowlist -> bounded download -> content hash/MIME/size/dimensions -> quality
review -> local thumbnail variants/crop -> credited manifest -> static publication.
Do not pick a similarly named player. Respect User-Agent/maxlag/Retry-After; stop
429 without changing accounts/hosts. Record failed candidates and revisit only
after the actual permitted interval. API traffic is never triggered per viewer.

Quality acceptance includes recognisable face, useful resolution, suitable crop,
no watermarks/rights-unknown content, duplicate detection and375/1440actual player
card/profile/compare checks. Originals stay private; approved derivatives have
appropriate attribution. Preserve initials/flag fallback. No AI-generated faces
standing in for actual athletes, Getty/news-agency imports or Google Images hotlinks.

Sources checked2026-10-29:

- https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia
- https://commons.wikimedia.org/wiki/Commons:Licensing
- https://www.wikidata.org/wiki/Wikidata:Licensing
- https://www.mediawiki.org/wiki/API:Etiquette
- https://docs.openverse.org/api/

Flickr API documentation was inaccessible in this research session; direct Flickr
automation remains unverified. No photo downloads or new public licence claims
were made during T041 planning. Report actual coverage, not candidate count.
