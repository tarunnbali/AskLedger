from sqlalchemy import text

from app.core.database import engine


def run_query(sql: str, entity_id: str):
    """
    Execute a validated SQL query.
    Sets the PostgreSQL session variable `app.current_tenant` before execution
    so that Row-Level Security (RLS) policies can enforce tenant isolation at
    the database level as a safety net.
    """
    # We create a raw core connection instead of an ORM session to ensure 
    # we have absolute control over the transaction isolation.
    with engine.connect() as conn:
        with conn.begin():
            # 1. Set the RLS variable for this specific connection ONLY
            conn.execute(text(f"SET app.current_tenant = '{entity_id}'"))
            
            # 2. Execute the user's validated query
            result = conn.execute(text(sql))
            
            # 3. SQLAlchemy 2.0+ requires row._mapping to convert to dict reliably
            rows = [dict(row._mapping) for row in result]
            
            # 4. As soon as the 'with' block exits, SQLAlchemy automatically rolls
            # back or clears the transaction state, blowing away the SET variable
            # before the connection is ever returned to the pool.
            return rows