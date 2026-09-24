"""
Test database setup.

Settings (and the SQLAlchemy engine) are created when app modules are first
imported, so the database has to exist before pytest collects any test. That
happens in pytest_configure:

  - CI: TEST_ADMIN_DATABASE_URL points at a Postgres service container.
  - Locally: without it, an embedded Postgres is started via `pgserver`.

A fresh `askledger_test` database gets the real schema, RLS policies and roles
(app.db_admin.setup_database), then the two-tenant fixture. The app connects as
the restricted askledger_app role, exactly like production.
"""
import os
import secrets
import tempfile

import pytest
from sqlalchemy import create_engine, make_url, text

# Placeholders for settings the tests never use for real (Gemini is mocked)
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-used")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-" + secrets.token_hex(8))
os.environ.setdefault("CHAT_RATE_LIMIT", "1000/minute")

TEST_DB = "askledger_test"
_state = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "isolation: tenant-isolation gate (needs Postgres)")

    admin_url = os.environ.get("TEST_ADMIN_DATABASE_URL")
    if not admin_url:
        import pgserver

        server = pgserver.get_server(tempfile.mkdtemp(prefix="askledger-pg-"), cleanup_mode="delete")
        _state["server"] = server
        admin_url = server.get_uri()

    server_url = make_url(admin_url)
    maintenance = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with maintenance.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    maintenance.dispose()

    admin_db_url = server_url.set(database=TEST_DB)
    app_password = secrets.token_urlsafe(24)
    app_db_url = admin_db_url.set(username="askledger_app", password=app_password)

    # Must be set before any `app` import creates the engine
    os.environ["DATABASE_URL"] = app_db_url.render_as_string(hide_password=False)
    _state["admin_url"] = admin_db_url.render_as_string(hide_password=False)

    from app.db_admin import setup_database
    from tests.fixtures import seed_two_tenants

    admin_engine = create_engine(admin_db_url)
    setup_database(admin_engine, app_password=app_password)
    seed_two_tenants(admin_engine)
    admin_engine.dispose()


@pytest.fixture(scope="session")
def admin_engine():
    engine = create_engine(_state["admin_url"])
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def app_engine():
    from app.core.database import engine

    return engine


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def login(client):
    def _login(username: str) -> dict:
        from tests.fixtures import PASSWORD

        r = client.post("/api/v1/auth/login", json={"username": username, "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login
