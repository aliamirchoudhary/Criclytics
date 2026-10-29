# Docker Official Python index verified via registry/Hub on 2026-10-29.
# Review regularly: pinning provides reproducibility, not perpetual safety.
FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements.txt && useradd --uid 1000 --create-home app
# .dockerignore allowlists both direct-checkout and staged contexts.
COPY . .
RUN mkdir -p /app/data/live && chown app:app /app/data/live
USER app
EXPOSE 7860
# Bounded initial configuration; hosted capacity requires measurement.
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "2", "--timeout", "120", "wsgi:app"]
