import getpass
from sqlalchemy import text, create_engine

# Prompt user for their postgres superuser password
pwd = getpass.getpass("Enter your postgres superuser password: ")
engine = create_engine(f"postgresql://postgres:{pwd}@localhost:5432/subscription_ai")

def apply_rls():
    with engine.begin() as conn:
        print("Dropping old policies (if they exist)...")
        conn.execute(text("DROP POLICY IF EXISTS tenant_isolation ON subscriptions;"))
        conn.execute(text("DROP POLICY IF EXISTS tenant_isolation ON subscription_financial_terms;"))
        conn.execute(text("DROP POLICY IF EXISTS tenant_isolation ON billing_schedules;"))
        conn.execute(text("DROP POLICY IF EXISTS tenant_isolation ON subscription_calculations;"))
        
        print("Applying FORCE RLS configuration...")
        with open("rls_setup.sql", "r") as file:
            sql_script = file.read()
            
            # Remove all comment lines before splitting by semicolon
            lines = [line for line in sql_script.split('\\n') if not line.strip().startswith('--')]
            clean_script = '\\n'.join(lines)
            
            for command in clean_script.split(';'):
                clean_command = command.strip()
                if clean_command:
                    conn.execute(text(clean_command + ";"))

    print("✅ RLS successfully forced securely via Python!")

if __name__ == "__main__":
    apply_rls()
