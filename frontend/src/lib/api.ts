const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// The backend runs on a free tier that sleeps when idle. While it wakes up,
// requests fail at the network level (the proxy's response has no CORS
// headers), so network errors are retried for up to this long.
const WAKE_TIMEOUT_MS = 75_000;
const WAKE_RETRY_DELAY_MS = 3_000;

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

/** One row of a query result: column name -> value. */
export type ResultRow = Record<string, unknown>;

/** One answered part of a multi-part question. */
export interface SubResult {
  question: string;
  sql_query: string | null;
  results: ResultRow[] | null;
  explanation: string;
}

export interface ChatResponse {
  type?: "conversation" | "data_query" | "clarification" | "multi_query";
  sql_query?: string | null;
  // Rows for a data query; answered parts for a multi-part question
  results?: ResultRow[] | SubResult[] | null;
  explanation?: string;
  prompt_version?: string;
}

export function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

/** Fire-and-forget ping so a sleeping backend starts waking before the user clicks. */
export function warmUpBackend() {
  fetch(`${API_BASE_URL}/health`).catch(() => {});
}

async function fetchWithWakeRetry(url: string, init: RequestInit, onWaking?: () => void): Promise<Response> {
  const deadline = Date.now() + WAKE_TIMEOUT_MS;
  let notified = false;
  for (;;) {
    try {
      return await fetch(url, init);
    } catch {
      // HTTP error responses resolve normally; only network failures land here.
      // If the backend is already awake, this wasn't a cold start, so don't
      // keep retrying (a retried chat request would spend LLM quota).
      // no-cors: resolves whenever the server answers, even if CORS would
      // block reading the response, so a CORS misconfiguration isn't
      // mistaken for a sleeping server. Rejects only when unreachable.
      const awake = await fetch(`${API_BASE_URL}/health`, { mode: "no-cors" }).then(() => true).catch(() => false);
      if (awake) {
        throw new Error("Something went wrong on the server. Please try again.");
      }
      if (Date.now() + WAKE_RETRY_DELAY_MS > deadline) {
        throw new Error("The server didn't respond. Please try again in a minute.");
      }
      if (!notified) {
        notified = true;
        onWaking?.();
      }
      await new Promise((r) => setTimeout(r, WAKE_RETRY_DELAY_MS));
    }
  }
}

export async function loginBackend(
  username: string,
  password: string = "password123",
  onWaking?: () => void
): Promise<string> {
  const url = `${API_BASE_URL}/auth/login`;
  try {
    const response = await fetchWithWakeRetry(
      url,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      },
      onWaking
    );
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Login failed: ${response.status}`);
    }
    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error("Login call failed:", error);
    throw new Error(errorMessage(error, "An unexpected error occurred during login."));
  }
}

export async function queryBackend(
  message: string,
  token: string,
  history: HistoryMessage[] = [],
  onWaking?: () => void
): Promise<ChatResponse> {
  const url = `${API_BASE_URL}/chat`;

  try {
    const response = await fetchWithWakeRetry(
      url,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ question: message, history }),
      },
      onWaking
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("unauthorized");
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    console.error("API call failed:", error);
    throw new Error(errorMessage(error, "An unexpected error occurred while contacting the server."));
  }
}
