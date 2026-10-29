"""Dependency-free public frontend configuration shared by Flask and static builds."""
import json
from urllib.parse import urlsplit


def api_base(value=""):
    value = str(value).strip().rstrip("/")
    if not value:
        return ""
    if any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("Invalid frontend API whitespace")
    parts = urlsplit(value)
    if parts.username or parts.password or parts.query or parts.fragment or parts.path or not parts.hostname:
        raise ValueError("Frontend API base must be an origin without credentials, path or query")
    local = parts.hostname in {"localhost", "127.0.0.1", "::1"}
    try:
        parts.port  # Validate even though the numeric port is not otherwise needed.
    except ValueError as error:
        raise ValueError("Invalid frontend API port") from error
    if parts.scheme != "https" and not (parts.scheme == "http" and local):
        raise ValueError("Frontend API requires HTTPS except loopback development")
    # Restrict the hostname alphabet before embedding the origin in CSP headers.
    if not all(c.isalnum() or c in ".-:" for c in parts.hostname) or any(ord(c) > 127 for c in value):
        raise ValueError("Invalid frontend API hostname")
    return value


def runtime_script(value=""):
    return "window.CRICLYTICS_CONFIG = Object.freeze(" + json.dumps({"apiBase": api_base(value)}, ensure_ascii=True) + ");\n"
