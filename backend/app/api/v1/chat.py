from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.chat_schema import ChatRequest
from app.services.nl_to_sql_service import generate_sql, fix_sql
from app.services.conversation_service import (
    classify_intent,
    generate_clarifying_question,
    generate_conversational_reply,
    generate_explanation,
)
from app.services.query_service import run_query
from app.utils.sql_validator import validate_sql, enforce_limit
from app.core.config import settings

router = APIRouter()


def _run_single_query(question: str, entity_id: str, history: list, username: str = "") -> dict:
    """
    Full pipeline for a single data question:
    generate SQL → validate → execute → explain.
    Returns a dict with sql_query, results, and explanation.
    """
    sql = generate_sql(question, history)

    # Check if the SQL generator itself flagged ambiguity
    if sql.upper().startswith("CLARIFICATION_NEEDED:"):
        clarification = sql[len("CLARIFICATION_NEEDED:"):].strip()
        return {"type": "clarification", "explanation": clarification, "sql_query": None, "results": None}

    validate_sql(sql)
    sql = enforce_limit(sql, settings.MAX_SQL_ROWS)

    try:
        results = run_query(sql, entity_id)
        final_sql = sql
    except Exception as e:
        fixed_sql = fix_sql(question, sql, str(e))
        validate_sql(fixed_sql)
        final_sql = enforce_limit(fixed_sql, settings.MAX_SQL_ROWS)
        try:
            results = run_query(final_sql, entity_id)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="The AI generated an invalid or complex query that could not be processed securely."
            )

    explanation = generate_explanation(question, final_sql, results, history, username)
    return {"sql_query": final_sql, "results": results, "explanation": explanation}


@router.post("/chat")
@limiter.limit(settings.CHAT_RATE_LIMIT)
def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    entity_id = str(current_user.entity_id)
    username = current_user.username
    history = chat_request.history or []

    # Step 1: Classify intent — returns {"intent": "...", "subqueries": [...]}
    classification = classify_intent(chat_request.question, history)
    intent = classification.get("intent", "data_query")

    # Step 2A: Conversational message
    if intent == "conversation":
        reply = generate_conversational_reply(chat_request.question, history, username)
        return {
            "type": "conversation",
            "explanation": reply,
            "sql_query": None,
            "results": None,
        }

    # Step 2B: Ambiguous question — ask a clarifying question
    if intent == "ambiguous":
        clarification = generate_clarifying_question(chat_request.question, history)
        return {
            "type": "clarification",
            "explanation": clarification,
            "sql_query": None,
            "results": None,
        }

    # Step 2C: Multi-query — run each sub-question independently
    if intent == "multi_query":
        subqueries = classification.get("subqueries", [])
        if not subqueries:
            # Fallback: treat as a single data query if splitting failed
            intent = "data_query"
        else:
            multi_results = []
            for sub_question in subqueries:
                result = _run_single_query(sub_question, entity_id, history, username)
                result["question"] = sub_question
                multi_results.append(result)

            return {
                "type": "multi_query",
                "results": multi_results,
                "sql_query": None,
                "explanation": f"I found answers to {len(multi_results)} separate questions.",
            }

    # Step 2D: Single data query
    result = _run_single_query(chat_request.question, entity_id, history, username)

    # If the SQL generator itself requested clarification
    if result.get("type") == "clarification":
        return result

    return {
        "type": "data_query",
        "sql_query": result["sql_query"],
        "results": result["results"],
        "explanation": result["explanation"],
    }