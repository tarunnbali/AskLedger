const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  type?: "conversation" | "data_query" | "clarification" | "multi_query";
  sql_query?: string | null;
  results?: any[] | null;
  explanation?: string;
}

export async function loginBackend(username: string, password: string = "password123"): Promise<string> {
  const url = `${API_BASE_URL}/auth/login`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Login failed: ${response.status}`);
    }
    const data = await response.json();
    return data.access_token;
  } catch (error: any) {
    console.error("Login call failed:", error);
    throw new Error(error.message || "An unexpected error occurred during login.");
  }
}

export async function queryBackend(
  message: string,
  token: string,
  history: HistoryMessage[] = []
): Promise<ChatResponse> {
  const url = `${API_BASE_URL}/chat`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ question: message, history }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("unauthorized");
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error: any) {
    console.error("API call failed:", error);
    throw new Error(error.message || "An unexpected error occurred while contacting the server.");
  }
}
