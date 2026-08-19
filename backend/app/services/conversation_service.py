"""
Intent classification and conversational response service.
Uses Gemini to classify user messages into 4 categories, generate clarifying 
questions for ambiguous inputs, handle conversational replies, and explain results.
"""
import json
from openai import OpenAI

from app.core.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)


def _format_history(history: list) -> str:
    if not history:
        return ""
    lines = ["Conversation so far:"]
    for msg in history:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"  {role}: {msg.content}")
    return "\n".join(lines) + "\n\n"


def classify_intent(message: str, history: list = []) -> dict:
    """
    Classify the user message into one of 4 intents.
    Returns { "intent": "...", "subqueries": [...] }

    Intents:
      - "conversation"  — greeting, thanks, small talk
      - "data_query"    — a single clear database question
      - "ambiguous"     — question is unclear (needs clarification before querying)
      - "multi_query"   — 2+ distinct database questions in one message
    """
    history_context = _format_history(history)

    prompt = f"""You are an intent classifier for a subscription billing chatbot.

{history_context}User message: "{message}"

Classify this message into EXACTLY ONE of these intents:

1. "conversation" — greeting, small talk, thanks, goodbye, questions about the bot
2. "data_query" — a single, clear question about subscription data (can have multiple filters like 'active AND monthly', that is still ONE query)
3. "ambiguous" — the question is too vague or could mean multiple things; a clarifying question is needed before querying the database. Also use this for OR-based questions where the user seems unsure.
4. "multi_query" — contains 2 or more DISTINCT questions about DIFFERENT data topics joined by "and", comma, or "also". Example: "show me pending subscriptions and when is my next payment" — these are two different topics.

IMPORTANT distinction:
- "active AND monthly subscriptions" = data_query (one question, multiple filters on the SAME topic)
- "pending subscriptions AND next payment date" = multi_query (two DIFFERENT data topics)
- "show me X or Y" = ambiguous (user is unsure)

DATA ISOLATION RULE:
- If the user asks about ANOTHER person's or organization's data (e.g. "show me Bob's subscriptions", "what does Alice have", "give me data for user X"), classify as "conversation". The system enforces strict per-user data isolation — users can ONLY access their own data.

If the intent is "multi_query", also split the message into individual sub-questions.

Return a JSON object ONLY with no markdown:
- For conversation/data_query/ambiguous: {{"intent": "<label>"}}
- For multi_query: {{"intent": "multi_query", "subqueries": ["<question 1>", "<question 2>"]}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip().strip("```json").strip("```").strip()

    try:
        result = json.loads(raw)
        intent = result.get("intent", "data_query").lower()
        # Validate
        valid = {"conversation", "data_query", "ambiguous", "multi_query"}
        if intent not in valid:
            intent = "data_query"
        return {
            "intent": intent,
            "subqueries": result.get("subqueries", [])
        }
    except Exception:
        # Safe fallback — treat as data query if classification fails
        return {"intent": "data_query", "subqueries": []}


def generate_clarifying_question(message: str, history: list = []) -> str:
    """
    Generate a targeted clarifying question when the user's intent is ambiguous.
    """
    history_context = _format_history(history)

    prompt = f"""You are a helpful AI assistant for a subscription billing platform.

{history_context}The user asked: "{message}"

This question is ambiguous — it could be interpreted in multiple ways or needs more detail.
Ask ONE short, specific clarifying question to understand exactly what the user wants.
Be concise (1 sentence max). Do not make assumptions. Do not answer the question yet.

Your clarifying question:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_conversational_reply(message: str, history: list = [], username: str = "") -> str:
    """
    Generate a friendly, conversational response for non-data messages.
    """
    history_context = _format_history(history)
    user_ref = f" {username.capitalize()}" if username else ""

    prompt = f"""You are a friendly, professional AI assistant for a subscription billing platform called "AskLedger".
You help users query their subscription data using natural language.

{history_context}The user's name is "{username}". Address them by name when appropriate.
The user has sent a conversational message (not a data query). Respond naturally and helpfully.
Keep your response concise (1-3 sentences). Be warm and professional.

If the user greets you, greet them back by name (e.g. "Hello{user_ref}!") and briefly mention what you can help with.
If the user asks what you can do, explain that you can help them query their subscription data, billing schedules, revenue metrics (MRR/ARR), financial terms, and more — all using natural language.
If the user says thanks or goodbye, respond politely.
If the user asks about another person's or organization's data, politely explain that for security and privacy reasons, you can only provide information about the currently logged-in user's own subscriptions and billing data.

User message: "{message}"

Your response:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def generate_explanation(question: str, sql: str, results: list, history: list = [], username: str = "") -> str:
    """
    Generate a natural language explanation of the query results.
    """
    # Pass up to 100 rows to the LLM to provide full context
    results_preview = str(results[:100]) if results else "No results found"
    row_count = len(results) if results else 0
    history_context = _format_history(history)

    # Detect if the user's message started with a greeting so we can respond in kind
    greeting_starters = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy"]
    question_lower = question.lower().strip()
    starts_with_greeting = any(question_lower.startswith(g) for g in greeting_starters)
    greeting_instruction = f'Start your response with a warm greeting using their name, e.g. "Hello {username.capitalize()}!".' if (starts_with_greeting and username) else ""

    prompt = f"""You are a helpful data analyst assistant. The user asked a question, and the system queried the database.
Summarize the results in a clear, conversational way. Be concise (2-4 sentences max).
Do NOT repeat the SQL query. Focus on directly answering the user's question based on the data.
Analyze the data carefully to understand its structure (e.g., are there multiple rows representing the same entity?). Ensure your final answer is mathematically accurate. Only include counts, totals, or summaries if they naturally address the user's specific question.
The user's name is "{username}". {greeting_instruction}

{history_context}User's question: "{question}"
Number of results: {row_count}
Sample data: {results_preview}

Your summary:"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        extra_body={
            "reasoning": {
                "effort": "medium",
                "exclude": True
            }
        }
    )

    return response.choices[0].message.content.strip()
