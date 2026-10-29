# T044: Licensed player imagery and quality pipeline

- Status: Planned
- Depends on: T017,T043
- Budget: $0, no card, no metered fallback

Read AGENTS.md, docs/AUDIT.md, docs/ARCHITECTURE.md, docs/GIT_WORKFLOW.md,
docs/CRICKET_PLATFORM_MASTER_PLAN.md and docs/PLATFORM_PLAN_REVIEW.md.

## Requirements

Resolve exact identities through reviewed Wikidata/Commons IDs; collect per-file licence/author/source metadata then bounded local thumbnail download; allow verified free-licensed Flickr or contributed alternatives; improve photo coverage without AI player faces.

## Acceptance and verification

Wrong-person/duplicate/rights-unknown files rejected;429/Retry-After stop; attributed cropped responsive assets and fallback verified375/1440; report real coverage/quality improvement.

## Limits and handoff

Do not hotlink or infer permission from Google/ICC images; retain provider originals privately.

Preserve originals/private data; local commits only on a new chained ticket branch.
No push/merge/remote mutation. Update this file, index and progress with actual
evidence. Failure leaves last good data/model selected; rollback disables the new
adapter/job and retains immutable artifacts. Mark implemented pending review, not Done.
