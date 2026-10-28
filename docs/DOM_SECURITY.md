# Legacy renderer security boundary

T003 vendors DOMPurify with its upstream licence and SHA256/version provenance
under static/js/vendor. Each HTML page loads it and security.js synchronously
before legacy inline/page scripts. There is no remote sanitizer dependency.

The transitional guard sanitizes legacy innerHTML and insertAdjacentHTML writes
using a detached clone of the receiving context. This preserves table rows while
removing scripts, event attributes, unsafe links and unsupported embedded content.
Missing sanitizer fails closed. A fixed capturing image-error listener replaces
dynamic code-bearing fallback attributes. Team crest uses DOM creation/listeners.
Shared escaping includes apostrophes, flag codes are constrained, profile image
URLs are checked and untrusted hosts/credentials are rejected.

Flask and static output share enforced object/base/frame/form/image policies.
The stricter script policy is report-only because trusted inline legacy controls
still exist; this is an explicit migration stage, not a claim of full strict CSP.
T012 must remove remaining inline code and the prototype guard once callers use
safe DOM builders directly. Do not add new raw HTML sinks as a long-term pattern.
The image-host allowlist is explicit; unsupported photos get a neutral fallback.

Run `python -m tools.browser_security` with Playwright and Chrome. It exercises
malicious script/event/URL/name fragments, apostrophes, contextual table rows,
and search/compare/profile rendering. Evidence is recorded as JSON under docs/audit.
External network assets are blocked in that run. Page/style visual acceptance and
full accessibility remain T011 work; no production deployment was performed.
