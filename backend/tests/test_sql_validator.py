import pytest

from app.utils.sql_validator import UnsafeSQLError, enforce_limit, validate_sql


@pytest.mark.parametrize("sql", [
    "SELECT * FROM subscriptions",
    "select count(*) from subscriptions where status = 'active'",
    "SELECT s.updated_at, s.created_at FROM subscriptions s",   # UPDATE only as a whole word
    "SELECT subscription_name FROM subscriptions;",              # one trailing semicolon is fine
])
def test_allows_read_only_selects(sql):
    assert validate_sql(sql) is True


@pytest.mark.parametrize("sql", [
    "DELETE FROM subscriptions",
    "UPDATE subscriptions SET status = 'cancelled'",
    "INSERT INTO users (username) VALUES ('x')",
    "DROP TABLE subscriptions",
    "TRUNCATE billing_schedules",
    "ALTER TABLE users ADD COLUMN x int",
    "GRANT SELECT ON users TO public",
    "SELECT 1; DROP TABLE subscriptions",                       # stacked statement
    "SELECT * FROM subscriptions; SELECT * FROM users",
    "WITH x AS (DELETE FROM subscriptions RETURNING *) SELECT * FROM x",
    "COPY subscriptions TO '/tmp/out'",
    "EXPLAIN ANALYZE SELECT 1",                                  # not a plain SELECT
])
def test_rejects_anything_that_is_not_a_single_select(sql):
    with pytest.raises(UnsafeSQLError):
        validate_sql(sql)


def test_enforce_limit_wraps_the_query_and_strips_semicolons():
    wrapped = enforce_limit("SELECT * FROM subscriptions;", 100)
    assert wrapped == "SELECT * FROM (SELECT * FROM subscriptions) AS safe_limit_wrapper LIMIT 100;"
