"""
Tenant-isolation gate: every test here tries to see data from the wrong tenant.

A failure means tenant data could leak, and CI blocks the merge. The tests go
through the same code paths as production: the restricted askledger_app role,
app.services.query_service.run_query, and the real /chat endpoint (with the
LLM replaced by stubs that return hostile SQL).
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db_admin import APP_ROLE, QUERY_ROLE, TENANT_TABLES
from tests.fixtures import SUBSCRIPTIONS, TENANT_A, TENANT_B

pytestmark = pytest.mark.isolation


def _expected_count(table: str, tenant) -> int:
    """Row counts implied by the fixture: one row per subscription, except schedules."""
    subs = SUBSCRIPTIONS[tenant]
    if table == "billing_schedules":
        return sum(periods for *_, periods in subs)
    return len(subs)


# ── Database configuration ────────────────────────────────────────────────────

def test_database_roles_cannot_bypass_rls(admin_engine):
    with admin_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname IN (:a, :q)"),
            {"a": APP_ROLE, "q": QUERY_ROLE},
        ).all()
    assert {r.rolname for r in rows} == {APP_ROLE, QUERY_ROLE}
    for r in rows:
        assert not r.rolsuper, f"{r.rolname} is a superuser, so RLS does not apply to it"
        assert not r.rolbypassrls, f"{r.rolname} has BYPASSRLS, so RLS does not apply to it"


def test_every_tenant_table_has_forced_rls(admin_engine):
    # Any table with an entity_id column is tenant data (except users, which login reads)
    with admin_engine.connect() as conn:
        tables = conn.execute(text("""
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                   (SELECT count(*) FROM pg_policies p WHERE p.tablename = c.relname) AS policies
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> 'users'
              AND EXISTS (SELECT 1 FROM information_schema.columns col
                          WHERE col.table_schema = 'public' AND col.table_name = c.relname
                            AND col.column_name = 'entity_id')
        """)).all()
    assert {t.relname for t in tables} >= set(TENANT_TABLES)
    for t in tables:
        assert t.relrowsecurity, f"RLS is not enabled on {t.relname}"
        assert t.relforcerowsecurity, f"RLS is not forced on {t.relname}"
        assert t.policies > 0, f"{t.relname} has no RLS policy"


def test_app_role_has_no_direct_access_to_tenant_tables(admin_engine):
    with admin_engine.connect() as conn:
        for table in TENANT_TABLES:
            allowed = conn.execute(
                text("SELECT has_table_privilege(:r, :t, 'SELECT')"), {"r": APP_ROLE, "t": table}
            ).scalar()
            assert not allowed, f"{APP_ROLE} can read {table} without switching to {QUERY_ROLE}"


# ── Queries through run_query ─────────────────────────────────────────────────

@pytest.mark.parametrize("table", TENANT_TABLES)
def test_each_tenant_sees_exactly_its_own_rows(table):
    from app.services.query_service import run_query

    for tenant in (TENANT_A, TENANT_B):
        rows = run_query(f"SELECT entity_id FROM {table}", str(tenant))
        assert rows, f"{table}: tenant {tenant} sees no rows at all"
        assert {str(r["entity_id"]) for r in rows} == {str(tenant)}, f"{table}: saw another tenant's rows"
        assert len(rows) == _expected_count(table, tenant)


def test_filtering_for_another_tenant_returns_nothing():
    from app.services.query_service import run_query

    rows = run_query(f"SELECT * FROM subscriptions WHERE entity_id = '{TENANT_B}'", str(TENANT_A))
    assert rows == []


def test_query_without_a_tenant_sees_nothing(app_engine):
    with app_engine.connect() as conn, conn.begin():
        conn.execute(text(f"SET LOCAL ROLE {QUERY_ROLE}"))
        for table in TENANT_TABLES:
            assert conn.execute(text(f"SELECT count(*) FROM {table}")).scalar() == 0, table


def test_tenant_setting_does_not_outlive_the_request(app_engine):
    """A pooled connection must not remember the previous request's tenant."""
    from app.services.query_service import run_query

    app_engine.dispose()  # start from an empty pool so the next checkout reuses the same connection
    run_query("SELECT 1", str(TENANT_A))
    with app_engine.connect() as conn:
        leftover = conn.execute(text("SELECT current_setting('app.current_tenant', true)")).scalar()
    assert leftover in (None, ""), f"tenant {leftover} is still set on a pooled connection"


def test_generated_sql_cannot_read_the_users_table():
    """users holds every tenant's usernames and password hashes and has no RLS."""
    from app.services.query_service import run_query

    with pytest.raises(DBAPIError, match="permission denied"):
        run_query("SELECT username, password_hash FROM users", str(TENANT_A))


# ── End to end through /chat, with the LLM stubbed ───────────────────────────

@pytest.fixture
def llm_returns(monkeypatch):
    """Make the chat pipeline run `sql` as if the LLM had generated it."""
    import app.api.v1.chat as chat

    def _set(sql: str):
        monkeypatch.setattr(chat, "classify_intent", lambda q, h: {"intent": "data_query", "subqueries": []})
        monkeypatch.setattr(chat, "generate_sql", lambda q, h: sql)
        monkeypatch.setattr(chat, "fix_sql", lambda q, s, e: sql)
        monkeypatch.setattr(chat, "generate_explanation", lambda *a, **k: "stub explanation")

    return _set


@pytest.mark.parametrize("user,tenant", [("alice", TENANT_A), ("bob", TENANT_B)])
def test_chat_unfiltered_query_returns_only_the_callers_rows(client, login, llm_returns, user, tenant):
    llm_returns("SELECT subscription_name, entity_id FROM subscriptions")
    r = client.post("/api/v1/chat", json={"question": "list everything", "history": []}, headers=login(user))
    assert r.status_code == 200, r.text
    rows = r.json()["results"]
    assert {row["entity_id"] for row in rows} == {str(tenant)}
    assert sorted(row["subscription_name"] for row in rows) == sorted(s[0] for s in SUBSCRIPTIONS[tenant])


def test_chat_cannot_reach_another_tenant_by_filtering(client, login, llm_returns):
    llm_returns(f"SELECT subscription_name FROM subscriptions WHERE entity_id = '{TENANT_B}'")
    r = client.post("/api/v1/chat", json={"question": "show Globex's data", "history": []}, headers=login("alice"))
    assert r.status_code == 200, r.text
    assert r.json()["results"] == []


def test_chat_cannot_read_password_hashes(client, login, llm_returns):
    llm_returns("SELECT username, password_hash, entity_id FROM users")
    r = client.post("/api/v1/chat", json={"question": "show all users", "history": []}, headers=login("alice"))
    assert r.status_code == 400, r.text
    assert "bob" not in r.text and "$2b$" not in r.text
