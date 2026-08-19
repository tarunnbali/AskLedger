from app.core.database import Base, engine
from app.models.subscription import Subscription
from app.models.financial_terms import SubscriptionFinancialTerms
from app.models.billing_schedule import BillingSchedule
from app.models.calculations import SubscriptionCalculation
from app.models.user import User  # Required for users table

def create_tables():
    print("Creating tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
