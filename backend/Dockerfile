# syntax=docker/dockerfile:1

# ── Build stage: install dependencies into an isolated prefix ────────────────
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ── Runtime stage: just Python, the installed packages and the app ───────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Pick up security fixes released since the base image was built
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Fixed, non-root UID so Kubernetes can enforce runAsNonRoot
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=builder /install /usr/local

WORKDIR /app
# Runtime code only: no tests, scripts or local .env
COPY --chown=app:app app ./app
COPY --chown=app:app prompts ./prompts
COPY --chown=app:app db ./db

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=4)"

# Render and most PaaS hosts inject the port via $PORT; exec so uvicorn is PID 1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
