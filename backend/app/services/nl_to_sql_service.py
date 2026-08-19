import re

from openai import OpenAI

from app.core.config import settings
from app.prompts.nl_to_sql_prompt import build_prompt

client = OpenAI(
    base_url=settings.GEMINI_BASE_URL,
    api_key=settings.GEMINI_API_KEY,
)


def clean_sql(text: str) -> str:
    """
    Strip markdown code fences that Gemini sometimes wraps SQL in.
    e.g.  ```sql\nSELECT ...\n```  →  SELECT ...
    """
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def generate_sql(question: str, history: list = []) -> str:
    """
    Returns either a raw SQL string, or a string starting with
    'CLARIFICATION_NEEDED:' if the model needs more information.
    """
    prompt = build_prompt(question, history)
    response = client.chat.completions.create(
        model=settings.GEMINI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()

    # Check if Gemini flagged the question as ambiguous
    if raw.upper().startswith("CLARIFICATION_NEEDED:"):
        return raw  # Pass through as-is — chat.py will handle it

    return clean_sql(raw)


def fix_sql(question: str, sql: str, error: str) -> str:
    retry_prompt = f"""The following SQL query failed.

User Question: {question}

Failed SQL:
{sql}

Database Error:
{error}

Fix the SQL query. Return ONLY the raw SQL, no markdown, no backticks, no explanations.
Only SELECT queries are allowed.
Do NOT include entity_id in the WHERE clause.
"""
    response = client.chat.completions.create(
        model=settings.GEMINI_MODEL,
        messages=[{"role": "user", "content": retry_prompt}]
    )
    return clean_sql(response.choices[0].message.content)