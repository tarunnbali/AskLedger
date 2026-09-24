"""
Seed demo data into the database at ADMIN_DATABASE_URL.

Run from backend/:  python -m scripts.seed_data
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from scripts.demo_data import DEMO_PASSWORD, seed_demo_data

load_dotenv(dotenv_path=".env")


def main():
    # Seeding needs INSERT rights the restricted app role doesn't have
    engine = create_engine(os.environ["ADMIN_DATABASE_URL"])
    summary = seed_demo_data(engine)
    print(f"Seeded {summary['subscriptions']} subscriptions across {len(summary['tenants'])} tenants.\n")
    for t in summary["tenants"]:
        print(f"  {t['name']} ({t['entity_id']})")
        print(f"    Users: {', '.join(t['users'])}   Login: {t['users'][0]} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
