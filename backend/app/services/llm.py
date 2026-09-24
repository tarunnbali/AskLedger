"""
Shared Gemini client with model fallback.

Free-tier quotas are per model, and individual models are sometimes
overloaded, so each call walks an ordered list of models and moves on to
the next one when a call is rate-limited or fails.
"""
import logging

import openai
from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# No SDK retries: on a 429 the SDK would sleep for Google's suggested retry
# delay (~40s) before retrying, which stalls the chat. Falling through to the
# next model immediately is faster. The timeout caps a hung or overloaded
# model: healthy calls finish in a few seconds, so 8s moves on quickly
# without cutting off normal responses.
client = OpenAI(
    base_url=settings.GEMINI_BASE_URL,
    api_key=settings.GEMINI_API_KEY,
    max_retries=0,
    timeout=8.0,
)


def complete(prompt: str, models: list[str]) -> str:
    last_error: Exception | None = None
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return (response.choices[0].message.content or "").strip()
        except openai.APIError as e:
            logger.warning("LLM call failed on %s: %s", model, e)
            last_error = e
    raise last_error
