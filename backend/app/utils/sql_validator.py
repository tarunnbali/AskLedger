import re

FORBIDDEN = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "COPY", "REPLACE", "EXECUTE", "CALL",
    "DO", "COMMIT", "ROLLBACK", "MERGE"
]


def validate_sql(sql: str):
    upper = sql.upper()

    # Reject complex multi-statements usually separated by semicolons
    if ";" in sql.strip().rstrip(";"):
         raise Exception("Multiple statements detected. Only secure, single SELECT queries allowed.")

    for keyword in FORBIDDEN:
        # Check for bounded whole words, e.g. stopping "UPDATE" but allowing "UPDATED_AT"
        if re.search(rf"\b{keyword}\b", upper):
            raise Exception(f"Unsafe SQL keyword detected.")

    if not upper.strip().startswith("SELECT"):
        raise Exception("Only SELECT queries allowed")

    return True


def enforce_limit(sql: str, limit: int):
    """
    Safely enforces a maximum row boundary.
    Instead of brittle regex string injection, it encapsulates the AI generated
    SQL as a subquery, ensuring the LIMIT is handled natively by the DB engine without
    breaking inner logic (like ORDER BY or GROUP BY closures).
    """
    cleaned = sql.strip().rstrip(";")
    return f"SELECT * FROM ({cleaned}) AS safe_limit_wrapper LIMIT {limit};"