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
from app.core.metrics import LLM_CALLS, LLM_TOKENS

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


def _outcome(error: openai.APIError) -> str:
    if isinstance(error, openai.RateLimitError):
        return "rate_limited"
    if isinstance(error, openai.APITimeoutError):
        return "timeout"
    if isinstance(error, openai.APIStatusError) and error.status_code >= 500:
        return "unavailable"
    return "error"


def complete(prompt: str, models: list[str], temperature: float | None = None) -> str:
    if not models:
        raise ValueError("no models configured")
    last_error: Exception | None = None
    for model in models:
        try:
            extra = {} if temperature is None else {"temperature": temperature}
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **extra,
            )
        except openai.APIError as e:
            logger.warning("LLM call failed on %s: %s", model, e)
            LLM_CALLS.labels(model, _outcome(e)).inc()
            last_error = e
            continue
        LLM_CALLS.labels(model, "ok").inc()
        if response.usage:
            LLM_TOKENS.labels(model, "prompt").inc(response.usage.prompt_tokens or 0)
            LLM_TOKENS.labels(model, "completion").inc(response.usage.completion_tokens or 0)
        return (response.choices[0].message.content or "").strip()
    raise last_error
