import pytest

import app.services.conversation_service as conv


@pytest.mark.parametrize("raw,expected", [
    ('{"intent": "conversation"}', "conversation"),
    ('```json\n{"intent": "data_query"}\n```', "data_query"),
    ('```\n{"intent": "ambiguous"}\n```', "ambiguous"),
    ('not json at all', "data_query"),               # unparseable falls back to a data query
    ('{"intent": "something_else"}', "data_query"),  # unknown labels fall back too
])
def test_intent_classifier_parses_model_output(monkeypatch, raw, expected):
    monkeypatch.setattr(conv, "complete", lambda prompt, models: raw)
    assert conv.classify_intent("anything")["intent"] == expected


def test_multi_query_keeps_its_subqueries(monkeypatch):
    raw = '```json\n{"intent": "multi_query", "subqueries": ["q1", "q2"]}\n```'
    monkeypatch.setattr(conv, "complete", lambda prompt, models: raw)
    assert conv.classify_intent("q1 and q2") == {"intent": "multi_query", "subqueries": ["q1", "q2"]}
