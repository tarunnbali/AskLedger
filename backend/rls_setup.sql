

-- Enable RLS on all data tables
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;

ALTER TABLE subscription_financial_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_financial_terms FORCE ROW LEVEL SECURITY;

ALTER TABLE billing_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_schedules FORCE ROW LEVEL SECURITY;

ALTER TABLE subscription_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_calculations FORCE ROW LEVEL SECURITY;

-- Create isolation policies (reads the session variable set by the backend)
-- The backend sets: SET app.current_tenant = '<entity_id>' before every query

CREATE POLICY tenant_isolation ON subscriptions
    USING (entity_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_isolation ON subscription_financial_terms
    USING (entity_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_isolation ON billing_schedules
    USING (entity_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_isolation ON subscription_calculations
    USING (entity_id = current_setting('app.current_tenant', true)::uuid);

-- ============================================================
-- HOW TO RUN:
-- psql -h <host> -p <port> -U postgres -d subscription_ai -f rls_setup.sql
-- ============================================================
