-- Row-Level Security for every tenant-owned table.
-- Idempotent: safe to re-run. Applied by app/db_admin.py (scripts/setup_database.py).
--
-- The backend sets the tenant per transaction with
--   SELECT set_config('app.current_tenant', '<entity_id>', true)
-- NULLIF makes the policy fail closed: when no tenant is set (the setting is
-- missing or reset to ''), the comparison is NULL and no rows are visible.

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON subscriptions;
CREATE POLICY tenant_isolation ON subscriptions
    USING (entity_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

ALTER TABLE subscription_financial_terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_financial_terms FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON subscription_financial_terms;
CREATE POLICY tenant_isolation ON subscription_financial_terms
    USING (entity_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

ALTER TABLE billing_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_schedules FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON billing_schedules;
CREATE POLICY tenant_isolation ON billing_schedules
    USING (entity_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);

ALTER TABLE subscription_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_calculations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON subscription_calculations;
CREATE POLICY tenant_isolation ON subscription_calculations
    USING (entity_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid);
