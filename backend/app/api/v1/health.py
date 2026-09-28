from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

# /api/v1/health: kept for existing health checks (Render)
router = APIRouter()

# Root-level probes, the conventional paths for Kubernetes and Prometheus
probes = APIRouter()


@router.get("/health")
@probes.get("/health")
def health():
    """Liveness: the process is up and serving requests."""
    return {"status": "ok"}


@probes.get("/ready")
def ready():
    """Readiness: dependencies needed to answer a question are available."""
    checks = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 — any failure means not ready
        checks["database"] = f"error: {type(exc).__name__}"

    try:
        from app.services.nl_to_sql_service import current_prompt

        checks["prompt"] = current_prompt().version
    except Exception as exc:  # noqa: BLE001
        checks["prompt"] = f"error: {type(exc).__name__}"

    ok = checks["database"] == "ok" and checks["prompt"] == settings.SQL_PROMPT_VERSION
    return JSONResponse({"status": "ready" if ok else "not ready", "checks": checks}, status_code=200 if ok else 503)


@probes.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
