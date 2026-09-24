"""
Database setup shared by scripts/setup_database.py, the tests and the evals.

Everything here needs an admin/owner connection. The running app never calls it.

Roles:
  askledger_app    LOGIN role the backend connects as. Reads `users` for login and
                   can switch into askledger_query. No direct access to tenant data.
  askledger_query  NOLOGIN role that chat queries run as (SET LOCAL ROLE). Can read
                   only the tenant tables, which Row-Level Security filters.
Neither role may bypass RLS: managed Postgres owner roles often have BYPASSRLS,
which silently disables tenant isolation.
"""
import re
from pathlib import Path

from sqlalchemy import Engine, text

from app.core.database import Base
from app.models import (  # noqa: F401  (register tables)
    billing_schedule,
    calculations,
    financial_terms,
    subscription,
    user,
)

APP_ROLE = "askledger_app"
QUERY_ROLE = "askledger_query"
TENANT_TABLES = ["subscriptions", "subscription_financial_terms", "billing_schedules", "subscription_calculations"]

RLS_SQL = Path(__file__).resolve().parent.parent / "db" / "rls.sql"

# Passwords are inlined into DDL (Postgres can't bind them), so only allow safe characters
_SAFE_PASSWORD = re.compile(r"^[A-Za-z0-9_\-]{16,128}$")


def create_schema(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


def apply_rls(engine: Engine) -> None:
    lines = [ln for ln in RLS_SQL.read_text().splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def _ensure_role(conn, name: str, login: bool, password: str | None) -> None:
    exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": name}).scalar()
    # NOINHERIT on the login role: membership in askledger_query must not grant
    # its table access implicitly, only through an explicit SET ROLE.
    attrs = f"{'LOGIN NOINHERIT' if login else 'NOLOGIN'} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE"
    if password is not None:
        if not _SAFE_PASSWORD.match(password):
            raise ValueError("password must be 16-128 characters of [A-Za-z0-9_-]")
        attrs += f" PASSWORD '{password}'"
    verb = "ALTER" if exists else "CREATE"
    conn.execute(text(f"{verb} ROLE {name} WITH {attrs}"))


def apply_roles(engine: Engine, app_password: str | None = None, revoke_legacy_grants: bool = True) -> None:
    """
    Create or update both roles and their grants.

    app_password: set/rotate askledger_app's password; None leaves it unchanged
    (a newly created role then has no password).
    revoke_legacy_grants: remove askledger_app's direct access to tenant tables.
    Older deployments granted it; only revoke once the running code uses
    askledger_query, or live queries will fail.
    """
    tables = ", ".join(TENANT_TABLES)
    with engine.begin() as conn:
        dbname = conn.execute(text("SELECT current_database()")).scalar()
        _ensure_role(conn, QUERY_ROLE, login=False, password=None)
        _ensure_role(conn, APP_ROLE, login=True, password=app_password)

        conn.execute(text(f'GRANT CONNECT ON DATABASE "{dbname}" TO {APP_ROLE}'))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}, {QUERY_ROLE}"))
        conn.execute(text(f"GRANT SELECT ON users TO {APP_ROLE}"))
        conn.execute(text(f"GRANT SELECT ON {tables} TO {QUERY_ROLE}"))
        conn.execute(text(f"REVOKE ALL ON users FROM {QUERY_ROLE}"))
        conn.execute(text(f"GRANT {QUERY_ROLE} TO {APP_ROLE}"))

        if revoke_legacy_grants:
            conn.execute(text(f"REVOKE ALL ON {tables} FROM {APP_ROLE}"))
            conn.execute(text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM {APP_ROLE}"))


def setup_database(engine: Engine, app_password: str | None = None, revoke_legacy_grants: bool = True) -> None:
    create_schema(engine)
    apply_rls(engine)
    apply_roles(engine, app_password=app_password, revoke_legacy_grants=revoke_legacy_grants)
