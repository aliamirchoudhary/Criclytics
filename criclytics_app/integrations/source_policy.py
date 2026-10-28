"""Fail-closed source rights gate. Tests may mock authorization; env flags cannot grant it."""
import json
from pathlib import Path


def decision():
    return json.loads(Path(__file__).with_name('live_source_policy.json').read_text(encoding='utf-8'))


def source_allowed(source):
    policy=decision()
    return source in policy.get('network_collectors_allowed',[])


def require_source(source):
    if not source_allowed(source):raise RuntimeError('Network source not approved; use historical replay or local manual mode')
