from sqlalchemy import text
from app.core.database import engine

def test_wrapper():
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SET app.current_tenant = '5855c775-969b-48da-8fe2-19ab1131c2c1';"))
            
            # This is the exact query Gemini generated from the user's terminal output:
            sql = "SELECT * FROM (SELECT s.id, s.subscription_id, s.subscription_name, s.plan_type, s.status, s.created_at FROM subscriptions AS s) AS safe_limit_wrapper LIMIT 100;"
            
            res = conn.execute(text(sql)).fetchall()
            print(f'Rows returned under active RLS using Gemini wrapper query: {len(res)}')

if __name__ == "__main__":
    test_wrapper()
