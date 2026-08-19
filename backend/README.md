# 🤖 AskLedger — Backend

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

An enterprise-ready, FastAPI-based backend that transforms natural language questions into secure PostgreSQL queries using Google Gemini. Architected specifically for multi-tenant SaaS environments, it enforces strict data isolation and SQL validation, guaranteeing that users can only query their own data.

## 🛠️ Tech Stack
| Component | Technology | Use Case |
|-----------|------------|----------|
| **Web framework** | **FastAPI** | High-performance API server with native async support and OpenAPI docs. |
| **Database ORM** | **SQLAlchemy 2.x** | Declarative models for the database and typed relationships. |
| **Database** | **PostgreSQL** | Primary datastore (requires `psycopg2-binary`). |
| **LLM for NL‑to‑SQL** | **Google Gemini** | LLM orchestrator leveraging Gemini's OpenAI-compatible endpoint via the `openai` SDK. |
| **Configuration** | **pydantic‑settings** | Strongly typed config parsing from `.env` files. |
| **Server** | **uvicorn** | ASGI web server. |

---

## 🔄 The Flow

```mermaid
flowchart TD
    Client([Client Application]) -->|POST /api/v1/chat| API[FastAPI Chat Endpoint]
    API -->|1. Generate SQL via Prompt| LLM((Gemini API))
    LLM -->|Returns Raw SQL| Validator[SQL Validator]
    
    Validator -->|2. Check Keywords| Wrapper[Query Wrapper]
    Wrapper -->|3. Wrap in LIMIT clause| Executor[Query Service]
    
    Executor -->|4. Set RLS & Execute| DB[(PostgreSQL)]
    DB -.->|Error| Retry[Retry Logic]
    Retry -.->|Fix SQL| LLM
    DB -->|Results| Executor
    
    Executor -->|5. Return JSON| Client
```

1. **Client Request:** Client sends a POST request with natural language (`What is my MRR?`).
2. **LLM Generation:** The backend merges the question with schema context and prompts the LLM for a raw SQL `SELECT` string.
3. **Validation & Wrapping:** The SQL undergoes strict anti-DML (Data Manipulation) keyword checks. It is then safely wrapped in a subquery `SELECT * FROM (<query>) LIMIT X` to guarantee performance.
4. **Execution:** The SQL executes through SQLAlchemy against PostgreSQL. If the query logically fails, the exception is quietly fed back to the LLM for exactly one self-correction attempt. 
5. **Response:** The valid results are transmitted back to the client.

---

## 🛡️ Tenant Isolation

This application uses a defense-in-depth approach, leaning entirely on **PostgreSQL Row-Level Security (RLS)** as the iron-clad failsafe.

1. **Authentication Token:** Each user request contains a validated JWT containing their specific company `entity_id`.
2. **Session Variable Injection:** Immediately before executing any natural language SQL, `query_service.py` sets a secure PostgreSQL environmental session variable:
   `db.execute(text(f"SET app.current_tenant = '{entity_id}'"))`
3. **RLS Interception:** Every database table (`subscriptions`, `billing_schedules`, etc.) has an active RLS policy defined via `rls_setup.sql`. The database implicitly transforms *every* `SELECT/JOIN` query to structurally require `WHERE entity_id = current_setting('app.current_tenant')`.
4. **Result:** Even if a user somehow maliciously engineers a query asking for all data (`SELECT * FROM subscriptions`), the database categorically refuses to yield rows not belonging to their `entity_id`.

---

## 🗄️ Database Design

The database tracks the core entities of a B2B SaaS architecture, interlinked by foreign keys and partitioned universally by `entity_id`.

```mermaid
erDiagram
    users {
        UUID id PK
        string username
        string password_hash
        UUID entity_id
    }
    subscriptions {
        UUID id PK
        string subscription_id
        string subscription_name
        string plan_type "monthly / annual"
        string status "active / cancelled"
        UUID organization_id
        UUID entity_id
    }
    subscription_financial_terms {
        UUID id PK
        UUID subscription_id FK
        float billing_amount
        string billing_frequency
        float discount_rate
        string currency
        UUID entity_id
    }
    billing_schedules {
        UUID id PK
        UUID subscription_id FK
        int billing_period
        date billing_start_date
        date billing_end_date
        float billing_amount
        UUID entity_id
    }
    subscription_calculations {
        UUID id PK
        UUID subscription_id FK
        string calculation_type "MRR / ARR"
        float total_revenue
        int contract_term_months
        int version
        boolean is_active
        UUID entity_id
    }

    subscriptions ||--o{ subscription_financial_terms : "Terms"
    subscriptions ||--o{ billing_schedules : "Schedules"
    subscriptions ||--o{ subscription_calculations : "Metrics"
```