"""
Shared plumbing for the SQL accuracy eval: a seeded benchmark database and
result comparison.

The database is built exactly like production (schema, RLS, roles) and seeded
with deterministic demo data, so the gold queries have stable answers. Dates are
relative to today on both sides (seed data and CURRENT_DATE in queries), so the
benchmark stays valid whichever day it runs.
"""
import itertools
import os
import secrets
import sys
import tempfile
import uuid
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, make_url, text

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

EVAL_DB = "askledger_eval"
# Fixed tenant IDs so seeded data (and therefore gold answers) are reproducible
TENANT_IDS = [uuid.UUID(f"{i:08x}-0000-4000-8000-{i:012x}") for i in range(1, 6)]
EVAL_TENANT = TENANT_IDS[0]  # Acme Corp, user alice
RNG_SEED = 42

_server = None


def prepare_database() -> str:
    """Create and seed the benchmark database. Returns its admin URL; sets DATABASE_URL for the app."""
    global _server
    admin_url = os.environ.get("TEST_ADMIN_DATABASE_URL")
    if not admin_url:
        import pgserver

        _server = pgserver.get_server(tempfile.mkdtemp(prefix="askledger-eval-pg-"), cleanup_mode="delete")
        admin_url = _server.get_uri()

    server_url = make_url(admin_url)
    maintenance = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with maintenance.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {EVAL_DB} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {EVAL_DB}"))
    maintenance.dispose()

    admin_db = server_url.set(database=EVAL_DB)
    password = secrets.token_urlsafe(24)
    os.environ["DATABASE_URL"] = admin_db.set(username="askledger_app", password=password).render_as_string(
        hide_password=False
    )
    os.environ.setdefault("JWT_SECRET", secrets.token_hex(16))
    os.environ.setdefault("GEMINI_API_KEY", "unset")

    from app.db_admin import setup_database  # imported only now: needs DATABASE_URL
    from scripts.demo_data import seed_demo_data

    engine = create_engine(admin_db)
    setup_database(engine, app_password=password)
    seed_demo_data(engine, tenant_ids=TENANT_IDS, rng_seed=RNG_SEED, today=date.today())
    engine.dispose()
    return admin_db.render_as_string(hide_password=False)


def run_as_tenant(sql: str, tenant: uuid.UUID = EVAL_TENANT) -> list[dict]:
    """Run SQL exactly like the app does: limit wrapper, query role, RLS."""
    from app.core.config import settings
    from app.services.query_service import run_query
    from app.utils.sql_validator import enforce_limit, validate_sql

    validate_sql(sql)
    return run_query(enforce_limit(sql, settings.MAX_SQL_ROWS), str(tenant))


def _norm(v):
    if isinstance(v, Decimal):
        v = float(v)
    if isinstance(v, float):
        return round(v, 2)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, uuid.UUID):
        return str(v)
    return v


def results_match(gold: list[dict], pred: list[dict], ordered: bool = False) -> bool:
    """
    True if `pred` contains the gold answer.

    Column names and extra columns don't matter: every gold column must match
    some predicted column value-for-value, row for row. Row order matters only
    when `ordered` (e.g. "top 3 by price").
    """
    if len(gold) != len(pred):
        return False
    if not gold:
        return True
    g = [[_norm(v) for v in row.values()] for row in gold]
    p = [[_norm(v) for v in row.values()] for row in pred]
    ncols_g, ncols_p = len(g[0]), len(p[0])

    def column(rows, i):
        return sorted(repr(r[i]) for r in rows)

    candidates = [[j for j in range(ncols_p) if column(p, j) == column(g, i)] for i in range(ncols_g)]
    if any(not c for c in candidates):
        return False

    gold_rows = [tuple(repr(v) for v in r) for r in g]
    for mapping in itertools.product(*candidates):
        pred_rows = [tuple(repr(r[j]) for j in mapping) for r in p]
        if ordered and pred_rows == gold_rows:
            return True
        if not ordered and Counter(pred_rows) == Counter(gold_rows):
            return True
    return False
