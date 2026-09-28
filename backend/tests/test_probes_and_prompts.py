import re

import pytest

from app.core.config import settings
from app.prompts.registry import available_versions, load_prompt
from app.services.nl_to_sql_service import build_prompt


def test_health_endpoints(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/v1/health").json() == {"status": "ok"}  # kept for Render


def test_ready_checks_the_database_and_prompt(client):
    r = client.get("/ready")
    assert r.status_code == 200, r.text
    assert r.json()["checks"] == {"database": "ok", "prompt": settings.SQL_PROMPT_VERSION}


def test_metrics_expose_request_and_llm_series(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert 'askledger_http_requests_total{method="GET",route="/health",status="200"}' in body
    for series in ("askledger_llm_calls_total", "askledger_sql_validation_rejections_total",
                   "askledger_chat_answers_total", "askledger_http_request_duration_seconds"):
        assert series in body


def test_configured_prompt_version_exists():
    assert settings.SQL_PROMPT_VERSION in available_versions("sql_generation")


@pytest.mark.parametrize("version", available_versions("sql_generation"))
def test_every_prompt_version_renders_completely(version):
    prompt = load_prompt("sql_generation", version)
    generated = build_prompt("How many active subscriptions do I have?", [], prompt)
    fixed = prompt.render("fix", question="q", sql="SELECT 1", error="boom")
    for text in (generated, fixed):
        assert not re.search(r"\{\{.*?\}\}", text), "unrendered placeholder"
    assert "How many active subscriptions do I have?" in generated
    assert "subscriptions" in prompt.fields["schema"]


def test_chat_answers_carry_the_prompt_version(client, login, monkeypatch):
    import app.api.v1.chat as chat

    monkeypatch.setattr(chat, "classify_intent", lambda q, h: {"intent": "conversation", "subqueries": []})
    monkeypatch.setattr(chat, "generate_conversational_reply", lambda *a, **k: "hello")
    r = client.post("/api/v1/chat", json={"question": "hi", "history": []}, headers=login("alice"))
    assert r.status_code == 200, r.text
    assert r.json()["prompt_version"] == settings.SQL_PROMPT_VERSION
