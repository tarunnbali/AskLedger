"""
Seed script: Creates logically consistent demo data for 5 tenants.

Status definitions:
  active    — subscription is live, has past + future billing dates
  cancelled — was active, user cancelled, all billing dates in the past
  pending   — new subscription awaiting activation, billing starts in near future

There is NO "inactive" status — it is redundant with "cancelled" in this domain.

Data consistency rules enforced:
  - active  → financial_terms exist, billing_schedules span past and future, calculations.is_active = TRUE
  - cancelled → financial_terms exist, billing_schedules all in the past, calculations.is_active = FALSE
  - pending → financial_terms exist, billing_schedules start 7-30 days from now, calculations.is_active = TRUE
  - billing_amount in financial_terms == billing_amount in billing_schedules
  - total_revenue in calculations = billing_amount × number_of_periods_in_contract
  - billing_schedule dates are contiguous (end of period N = start of period N+1)
"""

import os
import random
import uuid
from datetime import date, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.billing_schedule import BillingSchedule
from app.models.calculations import SubscriptionCalculation
from app.models.financial_terms import SubscriptionFinancialTerms
from app.models.subscription import Subscription
from app.models.user import User

# Seeding needs INSERT privileges the restricted app role doesn't have —
# use the admin/owner connection, not settings.DATABASE_URL.
load_dotenv(dotenv_path=".env")
admin_url = os.environ.get("ADMIN_DATABASE_URL") or os.environ["DATABASE_URL"]
engine = create_engine(admin_url)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

# ── Config ────────────────────────────────────────────────────────────────────
TODAY = date.today()
random.seed(42)

TENANTS = [uuid.uuid4() for _ in range(5)]
TENANT_NAMES = ["Acme Corp", "Globex Inc", "Initech LLC", "Soylent Corp", "Umbrella Corp"]

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

# How many billing periods to generate per plan type
PERIOD_DAYS = {"monthly": 30, "quarterly": 90, "annual": 365}


def _generate_billing_schedules(sub_id, entity_id, plan, status, base_price):
    """
    Generate billing schedules that make sense for the subscription's status.
    Returns a list of BillingSchedule objects.
    """
    schedules = []
    period_length = PERIOD_DAYS[plan]

    if status == "active":
        # Active: started 2-8 periods ago, extends 2-4 periods into future
        past_periods = random.randint(2, 8 if plan == "monthly" else 3)
        future_periods = random.randint(2, 4 if plan == "monthly" else 2)
        total_periods = past_periods + future_periods
        # Start date = today minus past_periods * period_length
        start = TODAY - timedelta(days=past_periods * period_length)

    elif status == "cancelled":
        # Cancelled: started in the past, ALL dates end before today
        total_periods = random.randint(2, 6 if plan == "monthly" else 2)
        # End of the last period should be in the past (at least 15 days ago)
        end_offset = random.randint(15, 120)
        start = TODAY - timedelta(days=(total_periods * period_length) + end_offset)

    elif status == "pending":
        # Pending: billing hasn't started yet — starts 7-30 days from now
        total_periods = random.randint(3, 12 if plan == "monthly" else 4)
        start = TODAY + timedelta(days=random.randint(7, 30))

    else:
        return schedules

    cursor = start
    for p in range(1, total_periods + 1):
        end = cursor + timedelta(days=period_length)
        schedules.append(BillingSchedule(
            subscription_id=sub_id,
            billing_period=p,
            billing_start_date=cursor,
            billing_end_date=end,
            billing_amount=base_price,
            entity_id=entity_id,
        ))
        cursor = end

    return schedules


try:
    # ── 1. USERS ──────────────────────────────────────────────────────────────
    first_names = [
        "Alice", "Bob", "Charlie", "Diana", "Eve",
        "Frank", "Grace", "Heidi", "Ivan", "Judy",
        "Mallory", "Niaj", "Olivia", "Peggy", "Sybil",
        "Trent", "Victor", "Walter", "Xavier", "Yvonne",
        "Zelda", "Aaron", "Brian", "Chloe", "David",
    ]

    pw_hash = hash_password("password123")
    users = []

    for i, name in enumerate(first_names):
        tenant_idx = i % len(TENANTS)
        users.append(User(
            username=name.lower(),
            password_hash=pw_hash,
            entity_id=TENANTS[tenant_idx],
        ))

    # Admin account for tenant 0
    users.append(User(
        username="admin",
        password_hash=hash_password("admin123"),
        entity_id=TENANTS[0],
    ))

    db.add_all(users)
    db.flush()

    # ── 2. SUBSCRIPTIONS + RELATED DATA ──────────────────────────────────────
    # Status distribution per tenant — roughly realistic
    # 60% active, 25% cancelled, 15% pending
    STATUS_WEIGHTS = ["active"] * 6 + ["cancelled"] * 2 + ["pending"] * 2

    sub_count = 0

    for tenant_id in TENANTS:
        num_subs = random.randint(6, len(PRODUCT_NAMES))
        used_names = set()

        for _ in range(num_subs):
            # Pick a product name not yet used for this tenant
            name = random.choice(PRODUCT_NAMES)
            while name in used_names:
                name = random.choice(PRODUCT_NAMES)
            used_names.add(name)

            plan = random.choice(["monthly", "annual", "quarterly"])
            status = random.choice(STATUS_WEIGHTS)

            # Subscription created_at should be in the past
            if status == "pending":
                created_at_offset = random.randint(1, 14)  # Created recently
            elif status == "cancelled":
                created_at_offset = random.randint(90, 600)  # Created long ago
            else:
                created_at_offset = random.randint(30, 400)  # Created a while back
            created_dt = TODAY - timedelta(days=created_at_offset)

            sub_count += 1
            sub = Subscription(
                subscription_id=f"SUB-{tenant_id.hex[:4].upper()}-{sub_count:04d}",
                subscription_name=name,
                plan_type=plan,
                status=status,
                organization_id=uuid.uuid4(),
                entity_id=tenant_id,
                created_at=created_dt,
            )
            db.add(sub)
            db.flush()  # Populate sub.id

            # ── Financial Terms ───────────────────────────────────────────────
            base_price = random.choice(PRICES[plan])
            discount = random.choice([0.0, 5.0, 10.0, 15.0, 20.0])
            # Cancelled subs might have had a full discount (100% = free trial)
            if status == "cancelled" and random.random() < 0.2:
                discount = 100.0

            fin = SubscriptionFinancialTerms(
                subscription_id=sub.id,
                billing_amount=base_price,
                billing_frequency=plan,
                discount_rate=discount,
                currency="USD",
                entity_id=tenant_id,
            )
            db.add(fin)

            # ── Billing Schedules ─────────────────────────────────────────────
            schedules = _generate_billing_schedules(sub.id, tenant_id, plan, status, base_price)
            db.add_all(schedules)

            # ── Calculations ──────────────────────────────────────────────────
            calc_type = "ARR" if plan == "annual" else "MRR"

            if plan == "monthly":
                contract_months = 12
                total_revenue = base_price * 12
            elif plan == "quarterly":
                contract_months = 12
                total_revenue = base_price * 4
            else:  # annual
                contract_months = 12
                total_revenue = base_price

            calc = SubscriptionCalculation(
                subscription_id=sub.id,
                calculation_type=calc_type,
                total_revenue=total_revenue,
                contract_term_months=contract_months,
                version=1,
                is_active=(status in ("active", "pending")),  # Active OR pending have live calculations
                entity_id=tenant_id,
            )
            db.add(calc)

    db.commit()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("✅ Seed data inserted successfully!")
    print(f"Generated {len(users)} users across {len(TENANTS)} tenants.")
    print(f"Generated {sub_count} subscriptions.\n")

    for t_idx, t_id in enumerate(TENANTS):
        t_users = [u.username for u in users if u.entity_id == t_id]
        t_subs_active = sum(1 for _ in db.query(Subscription).filter(
            Subscription.entity_id == t_id, Subscription.status == "active"
        ))
        t_subs_cancelled = sum(1 for _ in db.query(Subscription).filter(
            Subscription.entity_id == t_id, Subscription.status == "cancelled"
        ))
        t_subs_pending = sum(1 for _ in db.query(Subscription).filter(
            Subscription.entity_id == t_id, Subscription.status == "pending"
        ))

        print(f"  📁 {TENANT_NAMES[t_idx]} ({t_id})")
        print(f"     Users: {', '.join(t_users)}")
        print(f"     Subs:  active={t_subs_active}, cancelled={t_subs_cancelled}, pending={t_subs_pending}")
        print(f"     Login: {t_users[0]} / password123")
        print()

except Exception as e:
    db.rollback()
    print(f"❌ Seed failed: {e}")
    raise
finally:
    db.close()
