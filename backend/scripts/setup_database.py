"""
Create tables, apply Row-Level Security and set up the database roles.

Run from backend/ with ADMIN_DATABASE_URL (owner connection) in .env:
  python -m scripts.setup_database                     # idempotent: schema, RLS, roles
  python -m scripts.setup_database --rotate-password   # also set a new askledger_app password
  python -m scripts.setup_database --keep-legacy-grants
      Leaves askledger_app's old direct access to tenant tables in place. Use it
      for the first run on an existing deployment, before the code that queries
      through askledger_query is live; run again without it afterwards.
"""
import argparse
import os
import secrets

from dotenv import load_dotenv
from sqlalchemy import create_engine, make_url

from app.db_admin import APP_ROLE, setup_database

load_dotenv(dotenv_path=".env")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rotate-password", action="store_true", help="set a new password for askledger_app")
    parser.add_argument(
        "--keep-legacy-grants", action="store_true", help="don't revoke askledger_app's direct table access"
    )
    args = parser.parse_args()

    admin_url = os.environ["ADMIN_DATABASE_URL"]
    password = secrets.token_urlsafe(24) if args.rotate_password else None
    setup_database(create_engine(admin_url), app_password=password, revoke_legacy_grants=not args.keep_legacy_grants)
    print("Schema, Row-Level Security and roles are up to date.")

    if password:
        app_url = make_url(admin_url).set(username=APP_ROLE, password=password)
        print("\nNew DATABASE_URL for the app (put it in .env and your host's environment):")
        print(app_url.render_as_string(hide_password=False))


if __name__ == "__main__":
    main()
