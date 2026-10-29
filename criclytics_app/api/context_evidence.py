"""Local-only public-scope observations; never accepts notes, identities or writes."""
from datetime import datetime, timezone
import sqlite3
from flask import Blueprint,current_app,jsonify,request
from werkzeug.exceptions import BadRequest
from ..services.annotations import position
from ..services.context_availability import summarize
from ..services.match_context import ContextLedger
from ..services.weather import utc
from ..web.local_access import is_local_request

bp = Blueprint('context_evidence',__name__)


@bp.get('/api/v1/context-evidence')
def evidence():
    allowed = {'match_id','before_event_id','as_of','venue_id','team_id'}
    if set(request.args)-allowed:
        raise BadRequest('Only public context selectors are accepted')
    cutoff = request.args.get('as_of') or datetime.now(timezone.utc).isoformat()
    target = request.args.get('before_event_id','')
    match_id = request.args.get('match_id','')
    try:
        if utc(cutoff)>datetime.now(timezone.utc) or position(target)[0]!=match_id:
            raise ValueError('Context requires a nonfuture cutoff and same-match target attempt')
    except (ValueError,TypeError):
        raise BadRequest('Context requires a nonfuture cutoff and same-match target attempt') from None
    records = []
    store = current_app.config['CONTEXT_LEDGER']
    available = bool(store and is_local_request())
    if available:
        ledger = None
        try:
            ledger = ContextLedger(store,read_only=True)
            records = ledger.eligible(match_id,cutoff,require_ingested=True)
        except (OSError,ValueError,sqlite3.Error):
            available = False
        finally:
            if ledger:ledger.close()
    result = summarize(records,cutoff,request.args.get('venue_id',''),request.args.get('team_id',''),target)
    result.update(available=available,local_only=True)
    response = jsonify(result)
    response.headers['Cache-Control']='no-store'
    return response
