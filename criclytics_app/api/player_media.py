"""Allowlisted portrait serving, separate from private data directories."""
from flask import Blueprint, current_app, jsonify, send_file, abort

bp = Blueprint('player_media', __name__)


@bp.get('/api/player-media')
def catalog():
    entries = current_app.extensions['player_media']
    return jsonify({'available': bool(entries), 'players': [
        {'identity_id': key, 'name': item['name'], 'image_path': '/api/player-media/'+key,
         'source': item['source'], 'use_scope': item['use_scope']}
        for key, item in entries.items()]})


@bp.get('/api/player-media/<identity_id>')
def portrait(identity_id):
    item = current_app.extensions['player_media'].get(identity_id)
    if not item:
        abort(404)
    return send_file(item['path'], mimetype='image/png' if item['path'].suffix == '.png' else 'image/jpeg',
                     conditional=True, max_age=86400)
