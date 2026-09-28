"""
Demo data generator, shared by scripts/seed_data.py and the SQL accuracy evals.

Creates logically consistent subscription data for several tenants:
  active    — live, billing dates span past and future, active calculation
  cancelled — all billing dates in the past, inactive calculation
  pending   — billing starts 7-30 days from `today`, active calculation
Billing amounts match between financial terms and schedules, and schedule
periods are contiguous.

Given the same tenant IDs, rng_seed and `today`, the output is identical,
which is what makes the eval benchmark reproducible.
"""
import random
import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.billing_schedule import BillingSchedule
from app.models.calculations import SubscriptionCalculation
from app.models.financial_terms import SubscriptionFinancialTerms
from app.models.subscription import Subscription
from app.models.user import User

TENANT_NAMES = ["Acme Corp", "Globex Inc", "Initech LLC", "Soylent Corp", "Umbrella Corp"]

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve",
    "Frank", "Grace", "Heidi", "Ivan", "Judy",
    "Mallory", "Niaj", "Olivia", "Peggy", "Sybil",
    "Trent", "Victor", "Walter", "Xavier", "Yvonne",
    "Zelda", "Aaron", "Brian", "Chloe", "David",
]

PRODUCT_NAMES = [
    "Cloud Storage Team", "Cloud Storage Enterprise",
    "API Gateway Pro", "API Gateway Starter",
    "Compute Instance Medium", "Compute Instance Large",
    "Database Hosting Managed", "Premium Support SLA",
    "Analytics Dashboard Real-Time", "CI/CD Pipeline Pro",
    "Monitoring Suite Basic", "Monitoring Suite Advanced",
]

PRICES = {
    "monthly": [49.0, 99.0, 149.0, 199.0, 499.0],
    "quarterly": [129.0, 299.0, 499.0, 999.0],
    "annual": [490.0, 990.0, 1990.0, 4990.0, 9990.0],
}

PERIOD_DAYS = {"monthly": 30, "quarterly": 90, "annual": 365}

# 60% active, 20% cancelled, 20% pending
STATUS_WEIGHTS = ["active"] * 6 + ["cancelled"] * 2 + ["pending"] * 2

DEMO_PASSWORD = "password123"  # noqa: S105 — published demo login


def _schedules(rng, today, sub_id, entity_id, plan, status, price):
    period = PERIOD_DAYS[plan]
    if status == "active":
        past = rng.randint(2, 8 if plan == "monthly" else 3)
        total = past + rng.randint(2, 4 if plan == "monthly" else 2)
        start = today - timedelta(days=past * period)
    elif status == "cancelled":
        total = rng.randint(2, 6 if plan == "monthly" else 2)
        start = today - timedelta(days=total * period + rng.randint(15, 120))
    else:  # pending
        total = rng.randint(3, 12 if plan == "monthly" else 4)
        start = today + timedelta(days=rng.randint(7, 30))

    rows, cursor = [], start
    for p in range(1, total + 1):
        end = cursor + timedelta(days=period)
        rows.append(BillingSchedule(
            subscription_id=sub_id, billing_period=p, billing_start_date=cursor,
            billing_end_date=end, billing_amount=price, entity_id=entity_id,
        ))
        cursor = end
    return rows


def seed_demo_data(
    engine: Engine,
    tenant_ids: list[uuid.UUID] | None = None,
    rng_seed: int = 42,
    today: date | None = None,
) -> dict:
    """
    Insert users and subscription data. Needs an admin connection (INSERT rights).
    Returns {"tenants": [{"name", "entity_id", "users"}], "subscriptions": n}.
    """
    rng = random.Random(rng_seed)
    today = today or date.today()
    tenant_ids = tenant_ids or [uuid.uuid4() for _ in range(len(TENANT_NAMES))]
    summary = {"tenants": [], "subscriptions": 0}

    with Session(engine) as db:
        pw_hash = hash_password(DEMO_PASSWORD)
        users = [
            User(username=name.lower(), password_hash=pw_hash, entity_id=tenant_ids[i % len(tenant_ids)])
            for i, name in enumerate(FIRST_NAMES)
        ]
        users.append(User(username="admin", password_hash=hash_password("admin123"), entity_id=tenant_ids[0]))
        db.add_all(users)
        db.flush()

        count = 0
        for tenant_id in tenant_ids:
            names = rng.sample(PRODUCT_NAMES, rng.randint(6, len(PRODUCT_NAMES)))
            for name in names:
                plan = rng.choice(["monthly", "annual", "quarterly"])
                status = rng.choice(STATUS_WEIGHTS)
                created_offset = {"pending": (1, 14), "cancelled": (90, 600)}.get(status, (30, 400))
                count += 1
                sub = Subscription(
                    subscription_id=f"SUB-{tenant_id.hex[:4].upper()}-{count:04d}",
                    subscription_name=name,
                    plan_type=plan,
                    status=status,
                    organization_id=uuid.UUID(int=rng.getrandbits(128)),
                    entity_id=tenant_id,
                    created_at=datetime.combine(today - timedelta(days=rng.randint(*created_offset)), time()),
                )
                db.add(sub)
                db.flush()

                price = rng.choice(PRICES[plan])
                discount = rng.choice([0.0, 5.0, 10.0, 15.0, 20.0])
                if status == "cancelled" and rng.random() < 0.2:
                    discount = 100.0
                db.add(SubscriptionFinancialTerms(
                    subscription_id=sub.id, billing_amount=price, billing_frequency=plan,
                    discount_rate=discount, currency="USD", entity_id=tenant_id,
                ))
                db.add_all(_schedules(rng, today, sub.id, tenant_id, plan, status, price))

                periods_per_year = {"monthly": 12, "quarterly": 4, "annual": 1}[plan]
                db.add(SubscriptionCalculation(
                    subscription_id=sub.id,
                    calculation_type="ARR" if plan == "annual" else "MRR",
                    total_revenue=price * periods_per_year,
                    contract_term_months=12,
                    version=1,
                    is_active=status in ("active", "pending"),
                    entity_id=tenant_id,
                ))
        db.commit()
        summary["subscriptions"] = count

    # Built from plain values: the ORM objects are expired once the session closes
    usernames = [name.lower() for name in FIRST_NAMES]
    for i, tenant_id in enumerate(tenant_ids):
        members = [u for j, u in enumerate(usernames) if j % len(tenant_ids) == i] + (["admin"] if i == 0 else [])
        summary["tenants"].append({
            "name": TENANT_NAMES[i] if i < len(TENANT_NAMES) else f"Tenant {i + 1}",
            "entity_id": str(tenant_id),
            "users": members,
        })
    return summary
