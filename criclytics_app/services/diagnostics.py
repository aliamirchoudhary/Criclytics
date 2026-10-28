"""Bounded per-process telemetry; only fixed event names and route templates escape."""
from collections import Counter, deque
from threading import Lock
import json
import logging
import time
from pathlib import Path

REQUIRED = ('players_index.json','player_yearly.json','player_vs_opp.json','player_venues.json',
            'h2h.json','team_format_stats.json','team_venue_stats.json','venue_stats.json',
            'venue_batters.json','venue_bowlers.json','venue_insights.json','records.json','completed_matches.json')
EVENTS = frozenset(('cache_hit','cache_miss','cache_parse_failure','cache_store_failure','repository_hit',
                    'repository_parse','repository_parse_failure','refresh_disabled','refresh_backoff','provider_success',
                    'provider_error','provider_timeout','provider_parse_failure','quota_stop','stale_fallback'))


class Diagnostics:
    def __init__(self):
        self.started=time.monotonic()
        self._lock=Lock()
        self._counts=Counter()
        self._samples=deque(maxlen=256)

    def event(self,name):
        if name not in EVENTS: raise ValueError('Unknown diagnostic event')
        with self._lock: self._counts[name]+=1

    def observe(self,milliseconds,size,status):
        with self._lock: self._samples.append((round(milliseconds,3),int(size),int(status)))

    def snapshot(self):
        with self._lock:
            rows=list(self._samples)
            counts={name:self._counts[name] for name in sorted(EVENTS)}
        ordered=sorted(r[0] for r in rows)
        def percentile(p): return ordered[min(len(ordered)-1,int((len(ordered)-1)*p))] if ordered else None
        return {'scope':'this process; counters reset on restart','uptime_seconds':int(time.monotonic()-self.started),
                'events':counts,'recent_requests':len(rows),'sample_limit':256,
                'latency_ms':{'p50':percentile(.5),'p95':percentile(.95),'max':max(ordered) if ordered else None},
                'max_response_bytes':max((r[1] for r in rows),default=0)}


def readiness(app):
    repo=app.extensions['json_repository']
    states={name:repo.inspect(Path(app.config['PROCESSED_DIR'])/name) for name in REQUIRED}
    ready=all(state['state']=='valid' for state in states.values())
    # Artifact identity is only reported if present; no invented dataset/model version.
    manifest=repo.read(Path(app.config['PROCESSED_DIR'])/'manifest.json')
    version=manifest.get('schema_version') if isinstance(manifest,dict) else None
    cache=app.extensions['live_cache']
    entry=cache.entry('matches.json')
    age=max(0,int(cache.clock()-entry['written_at'])) if entry else None
    return {'ready':ready,'status':'ready' if ready else 'not_ready','required_artifacts':states,
            'dataset_schema_version':version,'model':{'available':False,'version':None},
            'optional_feed':{'enabled':bool(app.config['LIVE_FETCH_ENABLED']),'available':entry is not None,
                             'snapshot_age_seconds':age,'state':'degraded' if entry is None or age>120 else 'cached'},
            'limits':{'workers':1,'threads':2,'repository_files':repo.maximum,'cache_files':cache.maximum,
                      'request_body_bytes':app.config['MAX_CONTENT_LENGTH'],'telemetry_samples':256}}


def register(app):
    from flask import g, request
    app.logger.setLevel(logging.INFO)
    @app.before_request
    def start(): g.diagnostic_start=time.perf_counter()

    @app.after_request
    def observe(response):
        if not request.path.startswith('/api/'): return response
        elapsed=(time.perf_counter()-getattr(g,'diagnostic_start',time.perf_counter()))*1000
        size=response.calculate_content_length() or 0
        app.extensions['diagnostics'].observe(elapsed,size,response.status_code)
        # Never serialize raw URL/query, headers, body, exception text or credentials.
        event={'event':'http_request','request_id':getattr(g,'request_id','unknown'),
               'endpoint':request.endpoint or 'unmatched','method':request.method,
               'status':response.status_code,'milliseconds':round(elapsed,3),'response_bytes':size}
        app.logger.info(json.dumps(event,separators=(',',':')))
        return response
