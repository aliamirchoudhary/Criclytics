"""Production entry point: gunicorn --bind 0.0.0.0:7860 wsgi:app."""
from criclytics_app import create_app

app = create_app()
