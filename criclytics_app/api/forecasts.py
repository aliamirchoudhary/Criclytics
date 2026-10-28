"""Versioned local-only read/shadow API; no source ingestion or model upload."""
import ipaddress
import re
from urllib.parse import urlsplit
from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden

bp = Blueprint('forecasts', __name__)


def service(workspace_id):
    if not re.fullmatch(r'match:(manual|cricsheet):[A-Za-z0-9_-]{1,100}', workspace_id):
        raise BadRequest('Invalid workspace identifier')
    result = current_app.extensions['forecast_service']
    if result:
        # Both socket peer and Host must be local; do not trust forwarded headers.
        try: local = ipaddress.ip_address(request.remote_addr or '').is_loopback
        except ValueError: local = False
        host = urlsplit('//'+request.host).hostname
        if not local or host not in ('localhost', '127.0.0.1', '::1'):
            raise Forbidden('Experimental workspaces are local only')
        origin = request.headers.get('Origin')
        if (origin and origin != request.host_url.rstrip('/')) or request.headers.get('Sec-Fetch-Site') == 'cross-site':
            raise Forbidden('Use the same local origin for experimental workspaces')
    return result


def unavailable():
    return jsonify({'api_version': 1, 'available': False, 'forecast_allowed': False,
                    'blocked_reasons': ['experimental_workspace_disabled'], 'forecast': None,
                    'experimental': True, 'promoted': False})


@bp.get('/api/v1/workspaces/<workspace_id>/state')
def state(workspace_id):
    instance = service(workspace_id)
    return jsonify(instance.get_state(workspace_id)) if instance else unavailable()


@bp.get('/api/v1/workspaces/<workspace_id>/forecast')
def forecast(workspace_id):
    instance = service(workspace_id)
    return jsonify(instance.forecast(workspace_id)) if instance else unavailable()


@bp.get('/api/v1/workspaces/<workspace_id>/history')
def history(workspace_id):
    instance = service(workspace_id)
    if not instance: return unavailable()
    limit = int(request.args.get('limit', 50))
    if limit > 200: raise BadRequest('History limit must be1..200')
    return jsonify({'api_version': 1, 'forecasts': instance.history(workspace_id, limit), 'experimental': True})


@bp.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store, private'
    response.headers['Vary'] = 'Host'
    return response
