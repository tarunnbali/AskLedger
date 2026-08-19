"""
Creates (or rotates the password for) a restricted, RLS-respecting Postgres
role for the app to connect as at runtime.

Why this exists: many managed Postgres providers (Neon included) grant the
default "owner" role BYPASSRLS. That means `ALTER TABLE ... FORCE ROW LEVEL
SECURITY` in rls_setup.sql is silently ignored for that role — tenant
isolation looks like it's working in the schema but does nothing at query
time. Run this once against your admin/owner connection, then point the
app's DATABASE_URL at the role this script creates instead.

Usage:
    ADMIN_DATABASE_URL=<owner connection string> python setup_db_role.py

Prints the new role's connection string at the end — put that in .env as
DATABASE_URL. Keep ADMIN_DATABASE_URL only for create_tables.py,
rls_setup.sql, and seed_data.py; never give it to the running app.
"""
import os
import re
import secrets
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path=".env")

APP_ROLE = "askledger_app"

admin_url = os.environ.get("ADMIN_DATABASE_URL")
if not admin_url:
    print("ERROR: set ADMIN_DATABASE_URL (your Postgres owner/admin connection string).")
    sys.exit(1)

engine = create_engine(admin_url)
app_password = secrets.token_urlsafe(24)

with engine.begin() as conn:
    exists = conn.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = :role"), {"role": APP_ROLE}
    ).fetchone()

    if exists:
        conn.execute(text(f"ALTER ROLE {APP_ROLE} WITH PASSWORD :pw".replace(":pw", f"'{app_password}'")))
        print(f"Role '{APP_ROLE}' already existed — password rotated.")
    else:
        conn.execute(text(
            f"CREATE ROLE {APP_ROLE} WITH LOGIN PASSWORD '{app_password}' NOBYPASSRLS NOSUPERUSER;"
        ))
        print(f"Role '{APP_ROLE}' created (NOBYPASSRLS, NOSUPERUSER).")

    dbname = re.search(r"/([^/?]+)(\?|$)", admin_url).group(1)
    conn.execute(text(f'GRANT CONNECT ON DATABASE "{dbname}" TO {APP_ROLE};'))
    conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE};"))
    conn.execute(text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {APP_ROLE};"))
    conn.execute(text(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {APP_ROLE};"
    ))

# Rebuild the connection string with the new role, reusing host/db/params from admin_url
new_url = re.sub(r"^postgresql://[^:]+:[^@]+@", f"postgresql://{APP_ROLE}:{app_password}@", admin_url)

print("\nSet this as DATABASE_URL in your .env:")
print(new_url)
