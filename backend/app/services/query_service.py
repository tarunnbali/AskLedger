from sqlalchemy import text

from app.core.database import engine
from app.db_admin import QUERY_ROLE


def run_query(sql: str, entity_id: str):
    """
    Execute a validated, LLM-generated SQL query for one tenant.

    Everything happens inside a single transaction, and both settings are
    transaction-local, so nothing survives on the pooled connection afterwards:
      - SET LOCAL ROLE switches to askledger_query, which can read only the
        tenant tables (not `users` with its password hashes).
      - set_config(..., true) scopes app.current_tenant to this transaction;
        Row-Level Security filters every row by it.
    """
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(f"SET LOCAL ROLE {QUERY_ROLE}"))
            conn.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": entity_id})
            result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]
