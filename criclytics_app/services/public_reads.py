"""Bounded per-process public historical responses; never a collector or private cache."""
from collections import OrderedDict, Counter
from dataclasses import dataclass
import hashlib
from threading import Event, Lock
import time

from flask import Response, g, jsonify, request


ENDPOINTS = frozenset('api.'+name for name in (
    'get_players','get_player','get_teams','get_team','get_venues','get_venue',
    'get_team_venue_stats','get_rankings','get_records','get_h2h','get_insights',
    'compare_players','search','get_players_meta','get_player_meta','get_teams_meta','get_venues_meta'))


@dataclass(frozen=True)
class Entry:
    body: bytes
    etag: str
    expires: float


class PublicReads:
    def __init__(self, ttl=30, maximum=128, budget=8*1024*1024,
                 response_limit=512*1024, flights=32, wait=2, clock=time.monotonic):
        self.ttl, self.maximum, self.budget = ttl, maximum, budget
        self.response_limit, self.flight_limit, self.wait = response_limit, flights, wait
        self.clock, self.lock = clock, Lock()
        self.entries, self.pending, self.counts = OrderedDict(), {}, Counter()
        self.bytes = 0

    def acquire(self, key):
        """Return (hit entry, owner event, busy); followers never compute together."""
        for _ in range(2):
            with self.lock:
                entry = self.entries.get(key)
                if entry and entry.expires <= self.clock():
                    self.bytes -= len(self.entries.pop(key).body)
                    entry = None
                if entry:
                    self.entries.move_to_end(key)
                    self.counts['hit'] += 1
                    return entry, None, False
                event = self.pending.get(key)
                if event is None:
                    if len(self.pending) >= self.flight_limit:
                        self.counts['busy'] += 1
                        return None, None, True
                    event = self.pending[key] = Event()
                    self.counts['compute'] += 1
                    return None, event, False
                self.counts['coalesced'] += 1
            if not event.wait(self.wait):
                break
        with self.lock:
            self.counts['busy'] += 1
        return None, None, True

    def release(self, key, event, body=None):
        with self.lock:
            if self.pending.get(key) is not event:
                return
            if body is not None and len(body) <= min(self.response_limit,self.budget):
                previous = self.entries.pop(key,None)
                if previous:
                    self.bytes -= len(previous.body)
                while self.entries and (len(self.entries) >= self.maximum or self.bytes+len(body) > self.budget):
                    _, old = self.entries.popitem(last=False)
                    self.bytes -= len(old.body)
                    self.counts['evicted'] += 1
                self.entries[key] = Entry(body,hashlib.sha256(body).hexdigest(),self.clock()+self.ttl)
                self.bytes += len(body)
            del self.pending[key]
            event.set()

    def snapshot(self):
        with self.lock:
            return {'scope':'per worker; restart on dataset promotion', 'entries':len(self.entries),
                    'bytes':self.bytes,'in_flight':len(self.pending),'counts':dict(self.counts),
                    'limits':{'entries':self.maximum,'bytes':self.budget,'response_bytes':self.response_limit,
                              'in_flight':self.flight_limit,'ttl_seconds':self.ttl,'wait_seconds':self.wait}}


def register(app):
    # Tests that mutate local artifacts keep their original visibility unless
    # specifically exercising this response cache. Production selects immutable
    # dataset directories and restarts on promotion; TTL also bounds staleness.
    enabled = app.config.get('PUBLIC_READ_CACHE_ENABLED', not app.testing)
    cache = PublicReads()
    app.extensions['public_reads'] = cache

    def headers(response, etag, age):
        response.set_etag(etag)
        response.headers['Cache-Control'] = f'public, max-age={age}, must-revalidate'
        return response

    @app.before_request
    def read():
        if (not enabled or request.method != 'GET' or request.endpoint not in ENDPOINTS
                or request.headers.get('Authorization') or request.headers.get('Cookie')):
            return
        # Registered after the shared validation hook. No raw key is logged.
        key = (request.endpoint,request.path,tuple(sorted(request.args.items())))
        entry, event, busy = cache.acquire(key)
        if busy:
            response = jsonify(error='Public statistics are busy; retry shortly',code='READ_BUSY')
            response.status_code = 503
            response.headers['Retry-After'] = '2'
            response.headers['Cache-Control'] = 'no-store'
            return response
        if entry:
            response = Response(entry.body,mimetype='application/json')
            headers(response,entry.etag,max(0,int(entry.expires-cache.clock())))
            return response.make_conditional(request)
        g.public_read_owner = (key,event)

    @app.after_request
    def save(response):
        owner = getattr(g,'public_read_owner',None)
        if not owner:
            return response
        body = None
        if (response.status_code == 200 and response.mimetype == 'application/json'
                and 'no-store' not in response.headers.get('Cache-Control','')
                and not response.headers.get('Set-Cookie')):
            payload = response.get_json(silent=True)
            if not isinstance(payload,dict) or 'error' not in payload:
                body = response.get_data()
        cache.release(*owner,body)
        g.public_read_owner = None
        if body is not None and len(body) <= cache.response_limit:
            headers(response,hashlib.sha256(body).hexdigest(),cache.ttl)
            response.make_conditional(request)
        return response

    @app.teardown_request
    def unlock(_error):
        owner = getattr(g,'public_read_owner',None)
        if owner:
            cache.release(*owner)
            g.public_read_owner = None
