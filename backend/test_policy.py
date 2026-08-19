import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def print_policies():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'subscription_bot'),
        password=os.getenv('POSTGRES_PASSWORD', 'bot123'),
        dbname=os.getenv('POSTGRES_DB', 'subscription_ai'),
    )
    cur = conn.cursor()
    cur.execute("SELECT polname, polcmd, polqual, polwithcheck FROM pg_policy WHERE polrelid = 'subscriptions'::regclass;")
    policies = cur.fetchall()
    
    print('--- ACTIVE POLICIES ON SUBSCRIPTIONS ---')
    for p in policies:
        print(p)
        
    # Check if RLS is actually enabled
    cur.execute("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'subscriptions';")
    rls_status = cur.fetchone()
    print(f'RLS Enabled: {rls_status[0]}, Force RLS: {rls_status[1]}')
    
if __name__ == "__main__":
    print_policies()
