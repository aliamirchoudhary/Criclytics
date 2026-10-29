"""Loopback-only personal data gate; forwarded headers never grant access."""
import ipaddress
from urllib.parse import urlsplit
from flask import request


def is_local_request():
    try:
        if not ipaddress.ip_address(request.remote_addr or '').is_loopback:
            return False
    except ValueError:
        return False
    return (urlsplit('//'+request.host).hostname in ('localhost','127.0.0.1','::1')
        and request.headers.get('Sec-Fetch-Site')!='cross-site'
        and request.headers.get('Origin',request.host_url.rstrip('/'))==request.host_url.rstrip('/'))
