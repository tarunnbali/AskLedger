"""
Prometheus metrics, exposed at /metrics.

Route labels use the matched route template (e.g. /api/v1/chat), never the raw
path, to keep label cardinality bounded.
"""
from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "askledger_http_requests_total", "HTTP requests handled", ["method", "route", "status"]
)
HTTP_LATENCY = Histogram(
    "askledger_http_request_duration_seconds", "HTTP request latency", ["method", "route"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 15, 30, 60),
)
LLM_CALLS = Counter(
    "askledger_llm_calls_total", "LLM calls by model and outcome", ["model", "outcome"]
)
LLM_TOKENS = Counter(
    "askledger_llm_tokens_total", "LLM tokens used", ["model", "kind"]
)
SQL_REJECTIONS = Counter(
    "askledger_sql_validation_rejections_total", "Generated SQL rejected by the safety validator"
)
CHAT_ANSWERS = Counter(
    "askledger_chat_answers_total", "Chat responses by type", ["type", "prompt_version"]
)
SQL_EXECUTION_ERRORS = Counter(
    "askledger_sql_execution_errors_total", "Generated SQL that failed even after one self-correction",
    ["prompt_version"],
)
EMPTY_RESULTS = Counter(
    "askledger_sql_empty_results_total", "Data queries that returned no rows", ["prompt_version"]
)
