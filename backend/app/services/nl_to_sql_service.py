import re

from app.core.config import settings
from app.prompts.registry import Prompt, load_prompt
from app.services.llm import complete


def current_prompt() -> Prompt:
    return load_prompt("sql_generation", settings.SQL_PROMPT_VERSION)


def clean_sql(text: str) -> str:
    """
    Strip markdown code fences that Gemini sometimes wraps SQL in.
    e.g.  ```sql\nSELECT ...\n```  →  SELECT ...
    """
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _history_block(history: list) -> str:
    if not history:
        return ""
    lines = "".join(f"  {'User' if m.role == 'user' else 'Assistant'}: {m.content}\n" for m in history)
    return f"Conversation so far:\n{lines}\n"


def build_prompt(question: str, history: list | None = None, prompt: Prompt | None = None) -> str:
    prompt = prompt or current_prompt()
    return prompt.render("generate", schema=prompt.fields["schema"], history=_history_block(history), question=question)


def generate_sql(question: str, history: list | None = None, prompt: Prompt | None = None) -> str:
    """
    Returns either a raw SQL string, or a string starting with
    'CLARIFICATION_NEEDED:' if the model needs more information.
    """
    # Temperature 0: the same question should get the same SQL
    raw = complete(build_prompt(question, history, prompt), settings.sql_models, temperature=0)

    # Check if Gemini flagged the question as ambiguous
    if raw.upper().startswith("CLARIFICATION_NEEDED:"):
        return raw  # Pass through as-is — chat.py will handle it

    return clean_sql(raw)


def fix_sql(question: str, sql: str, error: str, prompt: Prompt | None = None) -> str:
    prompt = prompt or current_prompt()
    fix_prompt = prompt.render("fix", question=question, sql=sql, error=error)
    return clean_sql(complete(fix_prompt, settings.sql_models, temperature=0))
