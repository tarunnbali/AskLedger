import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

from app.core.database import Base
from app.models.subscription import Subscription
from app.models.financial_terms import SubscriptionFinancialTerms
from app.models.billing_schedule import BillingSchedule
from app.models.calculations import SubscriptionCalculation
from app.models.user import User  # Required for users table

# Creating tables needs CREATE privileges the restricted app role doesn't
# have — use the admin/owner connection, not settings.DATABASE_URL.
load_dotenv(dotenv_path=".env")
admin_url = os.environ.get("ADMIN_DATABASE_URL") or os.environ["DATABASE_URL"]
engine = create_engine(admin_url)


def create_tables():
    print("Creating tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
