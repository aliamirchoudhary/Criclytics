"""Enforced policy shared by Flask and static assets."""
from ..frontend import api_base


def policy(origin=""):
    origin = api_base(origin)
    return (
        "default-src 'self'; script-src 'self'; script-src-attr 'none'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'self'; form-action 'self'; "
        "style-src 'self'; font-src 'self'; img-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self'" + (" " + origin if origin else "")
    )


BASE_POLICY = policy()
# Compatibility import for offline legacy audit tools. The policy is now enforced.
SCRIPT_REPORT_POLICY = BASE_POLICY
