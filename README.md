# AskLedger

Ask your subscription billing data questions in plain English — no SQL required.

AskLedger is a natural-language analytics assistant for multi-tenant subscription billing platforms. Type a question like *"What's my MRR this quarter?"* or *"When's my next payment due?"* and get a conversational answer, backed by an LLM that translates the question into validated, read-only SQL and executes it against PostgreSQL with strict Row-Level Security enforcing per-tenant data isolation.

**[Live demo →](#)** *(link goes here once deployed)*

---

## How it works

1. You log in as one of the demo tenants (see below).
2. You ask a question in the chat widget.
3. The backend classifies the intent (small talk vs. a real data question vs. an ambiguous one vs. multiple questions at once), turns data questions into SQL via an LLM, validates the SQL is read-only, and runs it — with PostgreSQL Row-Level Security silently restricting results to your tenant's data only, no matter what the AI-generated query looks like.
4. The results come back as a natural-language answer, not raw rows.

See [walkthrough.md](walkthrough.md) for a detailed step-by-step trace of a request through the whole system.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js, React, Tailwind |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL with Row-Level Security |
| LLM | Google Gemini (free tier) via its OpenAI-compatible endpoint |
| Auth | JWT |

## Try it yourself (demo accounts)

Password for all demo accounts: `password123`

| Username | Tenant |
|---|---|
| `alice` | Acme Corp |
| `bob` | Globex Inc |
| `charlie` | Initech LLC |

Try asking things like:
- "What's my total active ARR?"
- "Show me all my cancelled subscriptions"
- "When's my next payment?"
- "What subscriptions do I have and what do they cost?"

## Running locally

```bash
git clone <your-repo-url>
cd askledger
```

**Backend**
```bash
cd backend
cp .env.example .env   # fill in DATABASE_URL, ADMIN_DATABASE_URL, GEMINI_API_KEY, JWT_SECRET
pip install -r requirements.txt
python create_tables.py
psql "$ADMIN_DATABASE_URL" -f rls_setup.sql
# If your provider's owner role has BYPASSRLS (e.g. Neon), also run:
#   python setup_db_role.py
# and use the DATABASE_URL it prints instead of the owner connection string.
python seed_data.py
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000.

## Security notes

- Tenant isolation is enforced at the **database layer** via PostgreSQL RLS (`rls_setup.sql`), not just in application code — even a malformed AI-generated query can't leak another tenant's rows.
- Generated SQL is restricted to read-only `SELECT` statements (blocklist of DML/DDL keywords + single-statement enforcement) and wrapped in a row-limited subquery before execution.
- The `/chat` endpoint is rate-limited per IP to protect against runaway LLM API costs on a public demo.

More detail in [backend/README.md](backend/README.md) and [backend/SCHEMA.md](backend/SCHEMA.md).
