"""Flask application factory. External feeds are explicitly opt-in."""
import os
from pathlib import Path

from .paths import PACKAGE_ROOT, PROJECT_ROOT


def create_app(config=None):
    # Static build tools import paths without needing backend dependencies.
    from dotenv import load_dotenv
    from flask import Flask
    from flask_cors import CORS

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    app = Flask(__name__, static_folder=str(PACKAGE_ROOT / "static"),
                template_folder=str(PACKAGE_ROOT / "templates"))
    app.config.from_mapping(
        PROCESSED_DIR=str(PROJECT_ROOT / "data" / "processed"),
        RAW_DIR=str(PROJECT_ROOT / "data" / "raw"),
        LIVE_DIR=str(PROJECT_ROOT / "data" / "live"),
        REFERENCE_DIR=str(PROJECT_ROOT / "data" / "static"),
        CRICAPI_KEY=os.getenv("CRICAPI_KEY", ""),
        REDIS_URL=os.getenv("REDIS_URL", ""),
        LIVE_FETCH_ENABLED=os.getenv("LIVE_FETCH_ENABLED", "0") == "1",
        INITIALIZE_ENGINE=True,
        MAX_CONTENT_LENGTH=64 * 1024,
        CORS_ORIGINS=[s.strip() for s in os.getenv(
            "CORS_ORIGINS", "https://criclytics.aliamirchoudhary.workers.dev"
        ).split(",") if s.strip()],
    )
    if config:
        app.config.update(config)
    from .api.validation import register as register_validation
    register_validation(app)
    Path(app.config["LIVE_DIR"]).mkdir(parents=True, exist_ok=True)
    app.extensions["redis"] = None
    if app.config["REDIS_URL"] and app.config["LIVE_FETCH_ENABLED"]:
        import redis
        app.extensions["redis"] = redis.from_url(
            app.config["REDIS_URL"], decode_responses=True,
            socket_connect_timeout=2, socket_timeout=2,
        )
    from .services.repository import JsonRepository
    from .services.live_cache import LiveCache
    app.extensions['json_repository'] = JsonRepository()
    app.extensions['live_cache'] = LiveCache(app.config['LIVE_DIR'], app.extensions['redis'])
    app.extensions["probability_engine"] = None
    if app.config["INITIALIZE_ENGINE"]:
        from .ml.probability import ProbabilityEngine
        app.extensions["probability_engine"] = ProbabilityEngine(app.config["PROCESSED_DIR"])

    from .api.routes import bp as api
    from .web.routes import bp as web
    app.register_blueprint(api)
    app.register_blueprint(web)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
         methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

    @app.after_request
    def security_headers(response):
        from .web.security import BASE_POLICY, SCRIPT_REPORT_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Content-Security-Policy"] = BASE_POLICY
            response.headers["Content-Security-Policy-Report-Only"] = SCRIPT_REPORT_POLICY
        return response

    return app
