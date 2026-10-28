"""Shared static/Flask CSP with a staged stricter script policy."""
BASE_POLICY = (
    "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'; "
    "img-src 'self' data: https://cdn.jsdelivr.net https://h.cricapi.com "
    "https://upload.wikimedia.org https://a.espncdn.com https://img1.hscicdn.com "
    "https://images.icc-cricket.com https://resources.pulse.icc-cricket.com"
)
SCRIPT_REPORT_POLICY = (
    "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com "
    "https://cdn.jsdelivr.net; script-src-attr 'none'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "connect-src 'self' https://aliamirchoudhary-criclytics-backend.hf.space"
)
