SCHEMA_CONTEXT = """
Tables and Columns:

1. subscriptions   [Alias: s]
   - id (UUID, PK) — internal unique identifier for the subscription
   - subscription_id (VARCHAR) — human-readable ID like "SUB-5855-0001"
   - subscription_name (VARCHAR) — product name, e.g. "Cloud Storage Pro"
   - plan_type (VARCHAR) — one of: "monthly", "annual", "quarterly"
   - status (VARCHAR) — one of: "active" (live, has future payments), "cancelled" (terminated, no future payments), "pending" (new, billing starts soon)
   - organization_id (UUID) — the client organization on this subscription
   - entity_id (UUID) — tenant identifier (DO NOT filter by this; backend enforces it automatically via Row-Level Security)
   - created_at (TIMESTAMP) — when the subscription was created

2. subscription_financial_terms   [Alias: sft]
   - id (UUID, PK)
   - subscription_id (UUID, FK → subscriptions.id)  [Relationship: Many-to-One with subscriptions]
   - billing_amount (NUMERIC) — base amount charged per billing cycle
   - billing_frequency (VARCHAR) — mirrors plan_type: "monthly", "annual", "quarterly"
   - discount_rate (NUMERIC) — percentage discount, e.g. 10.0 = 10%, 100.0 = 100% (free)
   - currency (VARCHAR) — e.g. "USD"
   - entity_id (UUID)

   Each subscription has exactly ONE set of financial terms.
   Cardinality: subscriptions (1) → subscription_financial_terms (1) [One-to-One]

3. billing_schedules   [Alias: bs]
   - id (UUID, PK)
   - subscription_id (UUID, FK → subscriptions.id)  [Relationship: Many-to-One with subscriptions]
   - billing_period (INTEGER) — sequential period number starting at 1 (e.g. 1st month, 2nd month)
   - billing_start_date (DATE) — when this billing period starts
   - billing_end_date (DATE) — when this billing period ends
   - billing_amount (NUMERIC) — amount charged for this specific period
   - entity_id (UUID)

   A monthly subscription with 6 periods will have 6 billing_schedules rows (one per month).
   Cardinality: subscriptions (1) → billing_schedules (Many) [One-to-Many]

4. subscription_calculations   [Alias: sc]
   - id (UUID, PK)
   - subscription_id (UUID, FK → subscriptions.id)  [Relationship: Many-to-One with subscriptions]
   - calculation_type (VARCHAR) — "ARR" (Annual Recurring Revenue) or "MRR" (Monthly Recurring Revenue)
   - total_revenue (NUMERIC) — total projected revenue for this subscription
   - contract_term_months (INTEGER) — contract length in months
   - version (INTEGER) — version number for this calculation snapshot
   - is_active (BOOLEAN) — TRUE if this is the currently active calculation version
   - entity_id (UUID)

   Cardinality: subscriptions (1) → subscription_calculations (Many) [One-to-Many]
   NOTE: is_active = TRUE for active AND pending subscriptions. FALSE only for cancelled ones.

Relationship Summary:
  subscriptions.id (PK)  ──1:1──  subscription_financial_terms.subscription_id (FK)
  subscriptions.id (PK)  ──1:M──  billing_schedules.subscription_id (FK)
  subscriptions.id (PK)  ──1:M──  subscription_calculations.subscription_id (FK)

  There are NO direct foreign keys between subscription_financial_terms, billing_schedules,
  and subscription_calculations — they all link exclusively through subscriptions.id.

Important Notes:
  - NEVER include entity_id in a WHERE clause. RLS enforces it automatically at the DB level.
  - Always SELECT only columns relevant to the question; avoid SELECT * in JOINs.
  - When JOINing billing_schedules, rows multiply per billing period. Use aggregation (SUM, MAX) if the user wants a summary.
  - For upcoming/next date questions, filter billing_start_date >= CURRENT_DATE and ORDER BY billing_start_date ASC.
  - For past/previous date questions, filter billing_end_date < CURRENT_DATE and ORDER BY billing_end_date DESC.
  - For revenue questions, JOIN subscription_calculations and always add WHERE sc.is_active = TRUE.
  - For discount questions, note discount_rate is a percentage (10.0 = 10%, 100.0 = free/fully discounted).
  - NULL values may exist in financial terms if a subscription has no pricing set yet — use COALESCE where appropriate.
  - When asked about "active" subscriptions, filter subscriptions.status = 'active'.
  - Always qualify column names with table aliases when JOINing to avoid ambiguous column errors (e.g., s.id, NOT just id).
"""


def build_prompt(question: str, history: list = []):

    history_block = ""
    if history:
        history_block = "Conversation so far:\n"
        for msg in history:
            role = "User" if msg.role == "user" else "Assistant"
            history_block += f"  {role}: {msg.content}\n"
        history_block += "\n"

    return f"""You are a PostgreSQL expert assistant for a multi-tenant subscription billing platform.

Your task is to convert the user's natural language question into a single, precise, read-only PostgreSQL SELECT query.

SQL Clause Order (strictly follow this):
  SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT

Rules:
1. Generate syntactically valid PostgreSQL queries only.
2. Return ONLY the raw SQL query — no explanations, no markdown code fences (```sql), no backticks, no commentary.
3. ONLY generate a SELECT query — never INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, or any DDL/DML.
04. NEVER add a WHERE clause for entity_id — Row-Level Security enforces it automatically at the database level.
5. ALWAYS qualify ALL column names with table aliases when multiple tables are involved (e.g. s.status, NOT just status).
6. Use appropriate JOINs when data from multiple tables is needed. Default to LEFT JOIN unless an INNER JOIN is clearly required.
7. For any question involving revenue, totals, or calculations, JOIN subscription_calculations and add WHERE sc.is_active = TRUE.
8. For aggregation questions (totals, counts, averages), use SUM(), COUNT(), AVG(), MIN(), MAX() with proper GROUP BY.
9. For date-based questions (upcoming, next, past, overdue), always compare against CURRENT_DATE.
   - For "next payment" questions WITHOUT a specific subscription named: JOIN subscriptions on billing_schedules, GROUP BY subscription to show the next upcoming billing date PER subscription. Do NOT use a bare global LIMIT 1 unless the user explicitly asks for a single result.
   - Example correct query for "when is my next payment?":
     SELECT s.subscription_name, MIN(bs.billing_start_date) AS next_payment_date, bs.billing_amount
     FROM billing_schedules bs JOIN subscriptions s ON s.id = bs.subscription_id
     WHERE bs.billing_start_date >= CURRENT_DATE
     GROUP BY s.subscription_name, bs.billing_amount
     ORDER BY next_payment_date ASC
10. Do not use SELECT * in a query with JOINs — always select specific named columns with their table alias prefix.
11. Use table aliases for all tables (s, sft, bs, sc) as defined in the schema.
12. IMPORTANT — If the question is too vague or ambiguous to answer correctly without making assumptions, return ONLY this exact text: CLARIFICATION_NEEDED: <your clarifying question here>
    This includes: questions mentioning "subscription" without specifying which one when only a single result is expected (e.g. "cancel my subscription", "what is my plan" with no name).

Schema:
{SCHEMA_CONTEXT}

{history_block}User Question:
{question}

SQL Query:"""
