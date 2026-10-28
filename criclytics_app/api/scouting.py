from flask import Blueprint,current_app,jsonify,request
from werkzeug.exceptions import BadRequest
from ..services.scouting import report

bp=Blueprint('scouting',__name__)


@bp.get('/api/v1/scouting')
def evidence():
    if set(request.args)-{'player','bowler','format','opponent','venue'}:
        raise BadRequest('Only public scouting selectors are accepted')
    if not request.args.get('player'):raise BadRequest('Player is required')
    fmt=request.args.get('format','T20I')
    if fmt not in ('T20I','ODI','Test'):raise BadRequest('Unsupported scouting format')
    return jsonify(report(current_app,request.args['player'],request.args.get('bowler'),fmt,
                          request.args.get('opponent',''),request.args.get('venue','')))
