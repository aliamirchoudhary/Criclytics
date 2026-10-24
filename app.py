"""Compatibility launcher: python app.py. Production uses wsgi:app."""
import os
from criclytics_app import create_app
app = create_app()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")))
