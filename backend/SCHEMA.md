# Database Schema Documentation

## Overview

The `subscription_ai` database is a **multi-tenant subscription billing system**. All data tables carry an `entity_id` column that maps to a tenant (company). Row-Level Security (RLS) filters every query to the calling user's tenant automatically — no application-level filtering is required.

---

## Entity-Relationship Diagram

```
┌──────────────────────────────────┐
│           subscriptions          │
│──────────────────────────────────│
│ id              UUID  (PK)       │
│ subscription_id VARCHAR           │
│ subscription_name VARCHAR         │
│ plan_type       VARCHAR           │
│ status          VARCHAR           │
│ organization_id UUID             │
│ entity_id       UUID  (RLS)      │
│ created_at      TIMESTAMP        │
└────────────┬─────────────────────┘
             │
             │ subscriptions.id (PK)
             │
    ┌────────┴────────────────────────────────────────────┐
    │                    │                                 │
    │ (1:1)              │ (1:M)                           │ (1:M)
    ▼                    ▼                                 ▼
┌──────────────────┐  ┌──────────────────────────┐  ┌────────────────────────────┐
│ subscription_    │  │   billing_schedules       │  │ subscription_calculations  │
│ financial_terms  │  │──────────────────────────│  │────────────────────────────│
│──────────────────│  │ id           UUID (PK)    │  │ id           UUID (PK)     │
│ id    UUID (PK)  │  │ subscription_id UUID (FK) │  │ subscription_id UUID (FK)  │
│ subscription_id  │  │ billing_period  INTEGER   │  │ calculation_type VARCHAR   │
│      UUID (FK)   │  │ billing_start_date DATE   │  │ total_revenue  NUMERIC     │
│ billing_amount   │  │ billing_end_date  DATE    │  │ contract_term_months INT   │
│      NUMERIC     │  │ billing_amount  NUMERIC   │  │ version        INTEGER     │
│ billing_frequency│  │ entity_id       UUID(RLS) │  │ is_active      BOOLEAN     │
│      VARCHAR     │  └──────────────────────────┘  │ entity_id      UUID (RLS)  │
│ discount_rate    │                                 └────────────────────────────┘
│      NUMERIC     │
│ currency VARCHAR │
│ entity_id  UUID  │
│      (RLS)       │
└──────────────────┘
```

---

## Tables in Detail

### 1. `subscriptions`
**The core table.** Every other table links back here.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Internal primary key |
| `subscription_id` | VARCHAR(50) | NOT NULL | Human-readable ID, e.g. `SUB-5855-0001`. The prefix (`5855`) matches the first 4 hex chars of the tenant's `entity_id` |
| `subscription_name` | VARCHAR(255) | NOT NULL | Product name, e.g. `Cloud Storage Pro` |
| `plan_type` | VARCHAR(50) | NOT NULL | One of: `monthly`, `annual`, `quarterly` |
| `status` | VARCHAR(50) | NOT NULL | One of: `active`, `inactive`, `cancelled`, `pending` |
| `organization_id` | UUID | NOT NULL | The client organization (company buying the subscription) |
| `entity_id` | UUID | NOT NULL | **Tenant identifier** — filtered automatically by RLS |
| `created_at` | TIMESTAMP | NOT NULL | Subscription creation timestamp |

---

### 2. `subscription_financial_terms`
**Pricing and billing terms for a subscription.** Each subscription has exactly one set of financial terms.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Internal primary key |
| `subscription_id` | UUID | FK → `subscriptions.id`, NOT NULL | Links to the parent subscription |
| `billing_amount` | NUMERIC | NOT NULL | The base amount charged per billing cycle (before discount) |
| `billing_frequency` | VARCHAR(50) | NOT NULL | Mirrors `plan_type`: `monthly`, `annual`, `quarterly` |
| `discount_rate` | NUMERIC | NOT NULL | Percentage discount. `0.0` = no discount, `10.0` = 10% off, `100.0` = fully free |
| `currency` | VARCHAR(10) | NOT NULL | Currency code, e.g. `USD` |
| `entity_id` | UUID | NOT NULL | **Tenant identifier** — filtered automatically by RLS |

**Cardinality:** `subscriptions` (1) ←→ (1) `subscription_financial_terms` — **One-to-One**

---

### 3. `billing_schedules`
**The payment calendar for a subscription.** Contains one row per billing period, giving a full timeline of when payments occur.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Internal primary key |
| `subscription_id` | UUID | FK → `subscriptions.id`, NOT NULL | Links to the parent subscription |
| `billing_period` | INTEGER | NOT NULL | Sequential period index starting at 1 (e.g. month 1, month 2…) |
| `billing_start_date` | DATE | NOT NULL | When this billing period begins |
| `billing_end_date` | DATE | NOT NULL | When this billing period ends |
| `billing_amount` | NUMERIC | NOT NULL | The amount due for this specific period |
| `entity_id` | UUID | NOT NULL | **Tenant identifier** — filtered automatically by RLS |

**Cardinality:** `subscriptions` (1) ←→ (M) `billing_schedules` — **One-to-Many**

> **Note:** A monthly subscription with 12 periods produces 12 rows here. JOINing to billing_schedules will multiply rows by the number of periods. Use aggregation (SUM, MAX, MIN) for summary queries.

---

### 4. `subscription_calculations`
**Revenue metrics (ARR/MRR) computed for a subscription.** Supports versioning — multiple snapshots can exist, but only one is active at any time.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, NOT NULL | Internal primary key |
| `subscription_id` | UUID | FK → `subscriptions.id`, NOT NULL | Links to the parent subscription |
| `calculation_type` | VARCHAR(50) | NOT NULL | `ARR` (Annual Recurring Revenue) or `MRR` (Monthly Recurring Revenue) |
| `total_revenue` | NUMERIC | NOT NULL | Total projected revenue for this subscription over its term |
| `contract_term_months` | INTEGER | NOT NULL | Contract length in months (1 = monthly, 3 = quarterly, 12 = annual) |
| `version` | INTEGER | NOT NULL | Version number of this calculation snapshot (starts at 1) |
| `is_active` | BOOLEAN | NOT NULL | `TRUE` for the current active version. Always filter `WHERE is_active = TRUE` to avoid double-counting |
| `entity_id` | UUID | NOT NULL | **Tenant identifier** — filtered automatically by RLS |

**Cardinality:** `subscriptions` (1) ←→ (M) `subscription_calculations` — **One-to-Many**

> **Warning:** Always add `WHERE sc.is_active = TRUE` when querying revenue. Without it, historical calculation versions are included and totals will be inflated.

---

## Relationship Summary

| Relationship | Type | Join Condition |
|---|---|---|
| `subscriptions` → `subscription_financial_terms` | **One-to-One** | `subscriptions.id = subscription_financial_terms.subscription_id` |
| `subscriptions` → `billing_schedules` | **One-to-Many** | `subscriptions.id = billing_schedules.subscription_id` |
| `subscriptions` → `subscription_calculations` | **One-to-Many** | `subscriptions.id = subscription_calculations.subscription_id` |

The three child tables (`subscription_financial_terms`, `billing_schedules`, `subscription_calculations`) are **not directly related to each other** — they all join exclusively through `subscriptions.id`.

---

## Row-Level Security (RLS)

Every data table has an `entity_id` UUID column and an active PostgreSQL RLS policy:

```sql
CREATE POLICY tenant_isolation ON <table>
    USING (entity_id = current_setting('app.current_tenant', true)::uuid);
```

Before every query, the backend sets:
```sql
SET app.current_tenant = '<logged_in_user_entity_id>';
```

This guarantees that **even a `SELECT *` query without any WHERE clause will only return rows belonging to the authenticated user's tenant.** The application code never needs to manually filter by `entity_id`.

---

## Common Query Patterns

### Get all subscriptions with pricing
```sql
SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status,
       sft.billing_amount, sft.discount_rate, sft.currency
FROM subscriptions s
LEFT JOIN subscription_financial_terms sft ON s.id = sft.subscription_id;
```

### Next upcoming payment date
```sql
SELECT bs.billing_start_date, bs.billing_amount
FROM billing_schedules bs
WHERE bs.billing_start_date >= CURRENT_DATE
ORDER BY bs.billing_start_date ASC
LIMIT 1;
```

### Total active ARR
```sql
SELECT SUM(sc.total_revenue) AS total_arr
FROM subscription_calculations sc
WHERE sc.calculation_type = 'ARR'
  AND sc.is_active = TRUE;
```

### Full subscription detail (all tables joined)
```sql
SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status,
       sft.billing_amount, sft.discount_rate, sft.currency,
       sc.calculation_type, sc.total_revenue
FROM subscriptions s
LEFT JOIN subscription_financial_terms sft ON s.id = sft.subscription_id
LEFT JOIN subscription_calculations sc ON s.id = sc.subscription_id AND sc.is_active = TRUE;
```
