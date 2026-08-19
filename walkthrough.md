# NL-to-SQL Chatbot: Complete End-to-End Flow

## Architecture Overview

```mermaid
flowchart LR
    subgraph Frontend["Next.js Frontend :3000"]
        A[Login Page] --> B[Chat Interface]
    end

    subgraph Backend["FastAPI Backend :8000"]
        C[Auth Endpoint] --> D[JWT Token]
        E[Chat Endpoint] --> F[get_current_user]
        F --> G[Gemini AI]
        G --> H[SQL Validator]
        H --> I[Query Service]
    end

    subgraph Database["PostgreSQL :5632"]
        J[(Tables with RLS)]
    end

    A -->|POST /auth/login| C
    D -->|Bearer Token| B
    B -->|POST /chat + JWT| E
    I -->|SET app.current_tenant + SQL| J
    J -->|Filtered Rows| B
```

---

## Phase 1: User Login (Authentication)

### Step 1 — User enters credentials on the frontend

The user opens `http://localhost:3000` and sees the **Login page** ([Login.tsx](file:///c:/Users/haard/Downloads/BOT/frontend/src/components/Login.tsx)). They type a username (e.g. `alice`) and password (`password123`).

### Step 2 — Frontend calls the backend login API

The [api.ts](file:///c:/Users/haard/Downloads/BOT/frontend/src/lib/api.ts) [loginBackend()](file:///c:/Users/haard/Downloads/BOT/frontend/src/lib/api.ts#9-28) function sends:

```http
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{ "username": "alice", "password": "password123" }
```

### Step 3 — Backend verifies credentials

In [auth.py](file:///c:/Users/haard/Downloads/BOT/backend/app/api/v1/auth.py):
1. Queries the `users` table for a row where `username = 'alice'`
2. Uses `bcrypt.checkpw()` from [security.py](file:///c:/Users/haard/Downloads/BOT/backend/app/core/security.py) to compare the plaintext password against the stored `password_hash`
3. If invalid → returns `401 Unauthorized`

### Step 4 — Backend generates a JWT token

If credentials are valid, [security.py](file:///c:/Users/haard/Downloads/BOT/backend/app/core/security.py) [create_access_token()](file:///c:/Users/haard/Downloads/BOT/backend/app/core/security.py#17-22) creates a JWT containing:

```json
{
  "sub": "a1b2c3d4-...",      // alice's user UUID
  "entity_id": "e5f6g7h8-...", // alice's TENANT UUID (e.g. Acme Corp)
  "exp": 1741782000            // expiry timestamp (60 min)
}
```

This token is **signed** with `JWT_SECRET` from [.env](file:///c:/Users/haard/Downloads/BOT/backend/.env) using HMAC-SHA256. Nobody can forge or tamper with it.

### Step 5 — Frontend stores the token in memory

The [page.tsx](file:///c:/Users/haard/Downloads/BOT/frontend/src/app/page.tsx) stores the token in React state (`sessionToken`). The UI switches from the Login view to the **Chat Interface**. The header now shows `Online as alice`.

---

## Phase 2: Asking a Question (The Chat Flow)

### Step 6 — User types a natural language question

In the [ChatInterface.tsx](file:///c:/Users/haard/Downloads/BOT/frontend/src/components/ChatInterface.tsx), the user types: **"Show me all active subscriptions"** and presses Enter.

### Step 7 — Frontend sends the question with the JWT

The [api.ts](file:///c:/Users/haard/Downloads/BOT/frontend/src/lib/api.ts) [queryBackend()](file:///c:/Users/haard/Downloads/BOT/frontend/src/lib/api.ts#29-57) function fires:

```http
POST http://localhost:8000/api/v1/chat
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{ "question": "Show me all active subscriptions" }
```

> [!IMPORTANT]
> The `Authorization: Bearer <token>` header is the **only** way the backend identifies who is asking. There is no tenant ID in the URL or request body — it comes exclusively from the cryptographically signed JWT.

---

## Phase 3: Backend Processing

### Step 8 — JWT verification & tenant extraction

Before the [chat.py](file:///c:/Users/haard/Downloads/BOT/backend/app/api/v1/chat.py) endpoint runs, FastAPI's dependency injection calls [dependencies.py](file:///c:/Users/haard/Downloads/BOT/backend/app/core/dependencies.py) [get_current_user()](file:///c:/Users/haard/Downloads/BOT/backend/app/core/dependencies.py#11-41):

1. Extracts the Bearer token from the `Authorization` header
2. Calls [decode_access_token(token)](file:///c:/Users/haard/Downloads/BOT/backend/app/core/security.py#24-29) — verifies signature + checks expiry
3. Reads `sub` (user ID) from the decoded payload
4. Queries `SELECT * FROM users WHERE id = <sub>`
5. Returns the full [User](file:///c:/Users/haard/Downloads/BOT/backend/app/models/user.py#10-26) object (which includes `entity_id`)

If any step fails → `401 Unauthorized` is returned immediately.

### Step 9 — Natural language → SQL via Google Gemini

In the chat endpoint, the backend calls [nl_to_sql_service.py](file:///c:/Users/haard/Downloads/BOT/backend/app/services/nl_to_sql_service.py) [generate_sql()](file:///c:/Users/haard/Downloads/BOT/backend/app/services/nl_to_sql_service.py#25-29):

1. Builds a detailed prompt using [nl_to_sql_prompt.py](file:///c:/Users/haard/Downloads/BOT/backend/app/prompts/nl_to_sql_prompt.py) containing:
   - The full database schema (table names, columns, types, relationships)
   - Strict rules (SELECT only, no entity_id filtering, valid PostgreSQL syntax)
   - The user's question
2. Sends this prompt to **Google Gemini** (`gemini-2.5-flash-lite`)
3. Gemini returns raw SQL, e.g.:
   ```sql
   SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status
   FROM subscriptions s
   WHERE s.status = 'active'
   ```

> [!NOTE]
> Notice how Gemini generates a **generic** query. It does NOT filter by `entity_id`. The prompt explicitly tells it: *"DO NOT include entity_id in the WHERE clause. The backend handles it automatically."* This is by design — tenant filtering happens at the database level.

### Step 10 — SQL validation & safety enforcement

The generated SQL passes through [sql_validator.py](file:///c:/Users/haard/Downloads/BOT/backend/app/utils/sql_validator.py):

1. **Forbidden keyword check**: Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, etc.
2. **SELECT-only check**: Query must start with `SELECT`
3. **Multi-statement check**: Rejects queries containing `;` (prevents SQL injection like `SELECT ...; DROP TABLE ...`)
4. **Row limit enforcement**: Wraps the query safely:
   ```sql
   SELECT * FROM (
     SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status
     FROM subscriptions s
     WHERE s.status = 'active'
   ) AS safe_limit_wrapper LIMIT 100;
   ```

---

## Phase 4: Tenant Isolation (The Critical Security Layer)

### Step 11 — Setting the PostgreSQL session variable

In [query_service.py](file:///c:/Users/haard/Downloads/BOT/backend/app/services/query_service.py), **immediately before** executing the SQL:

```python
db.execute(text(f"SET app.current_tenant = '{entity_id}'"))
result = db.execute(text(sql))
```

This sets a PostgreSQL **session-level variable** called `app.current_tenant` to Alice's `entity_id` UUID (e.g. `c8a95f41-5590-49ed-a4b9-9e85e0de3d29`).

### Step 12 — PostgreSQL RLS intercepts the query

The [rls_setup.sql](file:///c:/Users/haard/Downloads/BOT/backend/rls_setup.sql) has enabled **Row-Level Security** on every data table and created policies like:

```sql
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON subscriptions
    USING (entity_id::text = current_setting('app.current_tenant', true));
```

This policy means: **for every query on the `subscriptions` table, PostgreSQL will only return rows where `entity_id` matches the session variable `app.current_tenant`.**

### What actually happens inside PostgreSQL

When the query runs:
```sql
SELECT * FROM (
  SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status
  FROM subscriptions s WHERE s.status = 'active'
) AS safe_limit_wrapper LIMIT 100;
```

PostgreSQL's RLS engine **silently rewrites** it internally to behave like:
```sql
SELECT * FROM (
  SELECT s.subscription_id, s.subscription_name, s.plan_type, s.status
  FROM subscriptions s
  WHERE s.status = 'active'
    AND s.entity_id = 'c8a95f41-5590-49ed-a4b9-9e85e0de3d29'  -- ← ADDED BY RLS
) AS safe_limit_wrapper LIMIT 100;
```

> [!CAUTION]
> This filtering is **impossible to bypass** from the application level. Even if Gemini generated `SELECT * FROM subscriptions` (no WHERE clause at all), RLS would still filter out every row that doesn't belong to Alice's tenant. The database itself enforces isolation.

### Step 13 — Error recovery (self-healing)

If the AI-generated SQL fails (syntax error, wrong column name, etc.), [chat.py](file:///c:/Users/haard/Downloads/BOT/backend/app/api/v1/chat.py) catches the exception and calls [fix_sql()](file:///c:/Users/haard/Downloads/BOT/backend/app/services/nl_to_sql_service.py#31-48) which sends the original question, the failed SQL, and the error message back to Gemini for **one** self-correction attempt.

---

## Phase 5: Response to the User

### Step 14 — Backend returns JSON

The chat endpoint returns:
```json
{
  "sql_query": "SELECT * FROM (...) LIMIT 100;",
  "results": [
    {"subscription_id": "SUB-C8A9-0001", "subscription_name": "Cloud Storage Team", "plan_type": "monthly", "status": "active"},
    {"subscription_id": "SUB-C8A9-0003", "subscription_name": "API Gateway Pro", "plan_type": "annual", "status": "active"}
  ]
}
```

**These results contain ONLY Alice's tenant data.** Bob's, Charlie's, or any other tenant's subscriptions are completely invisible.

### Step 15 — Frontend renders the response

The [ChatMessage.tsx](file:///c:/Users/haard/Downloads/BOT/frontend/src/components/ChatMessage.tsx) component displays:
- The AI's response text
- A collapsible **"View Generated SQL"** section showing the exact query
- A styled **data table** with all returned rows

---

## Isolation Proof: Alice vs Bob

| | Alice (Acme Corp) | Bob (Globex Inc) |
|---|---|---|
| **Login** | `alice` / `password123` | `bob` / `password123` |
| **JWT entity_id** | `c8a95f41-...` | `d9b06a52-...` |
| **Session variable** | `SET app.current_tenant = 'c8a95f41-...'` | `SET app.current_tenant = 'd9b06a52-...'` |
| **Same question** | "Show all subscriptions" | "Show all subscriptions" |
| **Same SQL generated** | `SELECT * FROM subscriptions` | `SELECT * FROM subscriptions` |
| **RLS filter applied** | `WHERE entity_id = 'c8a95f41-...'` | `WHERE entity_id = 'd9b06a52-...'` |
| **Results** | Only Acme Corp's 8-15 subscriptions | Only Globex Inc's 8-15 subscriptions |

> [!IMPORTANT]
> Even though the AI generated the **exact same SQL** for both users, each user sees **completely different data** because PostgreSQL RLS applies different entity_id filters based on the session variable set from their JWT.

---

## Security Summary

| Layer | What It Does | Where |
|---|---|---|
| **JWT Authentication** | Verifies user identity, prevents impersonation | [dependencies.py](file:///c:/Users/haard/Downloads/BOT/backend/app/core/dependencies.py) |
| **SQL Validation** | Blocks INSERT/UPDATE/DELETE/DROP attacks | [sql_validator.py](file:///c:/Users/haard/Downloads/BOT/backend/app/utils/sql_validator.py) |
| **Row Limit** | Caps results at 100 rows to prevent data dumps | [sql_validator.py](file:///c:/Users/haard/Downloads/BOT/backend/app/utils/sql_validator.py) |
| **PostgreSQL RLS** | Database-level tenant isolation — unforgeable | [rls_setup.sql](file:///c:/Users/haard/Downloads/BOT/backend/rls_setup.sql) |
| **CORS** | Only allows requests from localhost:3000 | [main.py](file:///c:/Users/haard/Downloads/BOT/backend/app/main.py) |
