"""
A small, explicit two-tenant dataset for the isolation tests.

The tenants deliberately have different row counts in every table, so a test
that sees the wrong tenant's data (or both tenants' data) fails on the count.
"""
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.billing_schedule import BillingSchedule
from app.models.calculations import SubscriptionCalculation
from app.models.financial_terms import SubscriptionFinancialTerms
from app.models.subscription import Subscription
from app.models.user import User

TENANT_A = uuid.UUID("aaaaaaaa-0000-4000-8000-00000000000a")  # Acme, user alice
TENANT_B = uuid.UUID("bbbbbbbb-0000-4000-8000-00000000000b")  # Globex, user bob
PASSWORD = "password123"

# (name, plan, status, price, billing periods)
SUBSCRIPTIONS = {
    TENANT_A: [
        ("A Storage", "monthly", "active", 99.0, 4),
        ("A Gateway", "annual", "cancelled", 990.0, 1),
        ("A Compute", "quarterly", "pending", 299.0, 2),
    ],
    TENANT_B: [
        ("B Analytics", "monthly", "active", 499.0, 6),
        ("B Support", "annual", "active", 4990.0, 1),
    ],
}


def seed_two_tenants(engine: Engine) -> None:
    today = date.today()
    with Session(engine) as db:
        pw = hash_password(PASSWORD)
        db.add_all([
            User(username="alice", password_hash=pw, entity_id=TENANT_A),
            User(username="bob", password_hash=pw, entity_id=TENANT_B),
        ])
        for tenant, subs in SUBSCRIPTIONS.items():
            for i, (name, plan, status, price, periods) in enumerate(subs):
                sub = Subscription(
                    subscription_id=f"SUB-{tenant.hex[:4].upper()}-{i:04d}", subscription_name=name,
                    plan_type=plan, status=status, organization_id=uuid.uuid4(), entity_id=tenant,
                    created_at=datetime.combine(today - timedelta(days=60), datetime.min.time()),
                )
                db.add(sub)
                db.flush()
                db.add(SubscriptionFinancialTerms(
                    subscription_id=sub.id, billing_amount=price, billing_frequency=plan,
                    discount_rate=0.0, currency="USD", entity_id=tenant,
                ))
                for p in range(periods):
                    start = today + timedelta(days=30 * p)
                    db.add(BillingSchedule(
                        subscription_id=sub.id, billing_period=p + 1, billing_start_date=start,
                        billing_end_date=start + timedelta(days=30), billing_amount=price, entity_id=tenant,
                    ))
                db.add(SubscriptionCalculation(
                    subscription_id=sub.id, calculation_type="ARR" if plan == "annual" else "MRR",
                    total_revenue=price * 12, contract_term_months=12, version=1,
                    is_active=status != "cancelled", entity_id=tenant,
                ))
        db.commit()
