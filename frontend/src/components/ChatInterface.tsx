"use client";

import { useState, useRef, useEffect } from "react";
import { Sparkles } from "lucide-react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { queryBackend } from "@/lib/api";

const SUGGESTIONS = [
  "What's my total active ARR?",
  "Show me all my cancelled subscriptions",
  "When's my next payment due?",
  "Show me my pending subscriptions and my next payment date",
];

type MessageRole = "user" | "assistant" | "error";

interface Message {
  id: string;
  role: MessageRole;
  text: string;
  sql?: string | null;
  results?: any[] | null;
  // For multi_query responses — array of sub-results
  multiResults?: Array<{
    question: string;
    sql_query: string | null;
    results: any[] | null;
    explanation: string;
  }> | null;
}

export default function ChatInterface({ token }: { token: string }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hi! I'm AskLedger — ask me anything about your subscriptions, billing, or revenue in plain English, and I'll turn it into a secure query and answer you directly. You'll only ever see your own tenant's data.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const handleSendMessage = async (query: string) => {
    if (!query.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString() + "-user",
      role: "user",
      text: query,
    };

    // Build last 5 exchange history to send with request
    const history = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .slice(-10) // last 5 exchanges = 10 messages (user+assistant pairs)
      .map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.text,
      }));

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await queryBackend(query, token, history);

      let assistantMessage: Message;

      if (response.type === "multi_query") {
        // Multi-query: render a summary + sub-results stored separately
        const multiResults = (response as any).results as Array<{
          question: string;
          sql_query: string | null;
          results: any[] | null;
          explanation: string;
        }>;
        assistantMessage = {
          id: Date.now().toString() + "-assistant",
          role: "assistant",
          text: `I found answers to ${multiResults.length} separate questions:`,
          sql: null,
          results: null,
          multiResults,
        };
      } else if (response.type === "clarification") {
        // Clarifying question
        assistantMessage = {
          id: Date.now().toString() + "-assistant",
          role: "assistant",
          text: response.explanation || "Could you clarify your question?",
          sql: null,
          results: null,
        };
      } else {
        // Normal data_query or conversation
        assistantMessage = {
          id: Date.now().toString() + "-assistant",
          role: "assistant",
          text: response.explanation || "Here are your results:",
          sql: response.type === "data_query" ? response.sql_query : null,
          results: response.type === "data_query" ? response.results : null,
        };
      }

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: Date.now().toString() + "-error",
        role: "error",
        text: err.message || "Failed to execute query. Please check your connection to the backend.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full glass-panel mt-4 mb-4 rounded-2xl overflow-hidden shadow-1xl transition-all duration-300 border border-white/10">
      {/* Messages Window */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth"
      >
        {messages.map((msg) => (
          <ChatMessage key={msg.id} {...msg} />
        ))}

        {/* Suggestion chips — only before the first real exchange */}
        {messages.length === 1 && !loading && (
          <div className="pl-4 pr-1 animate-fade-in" style={{ animationDelay: "150ms" }}>
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-gray-500 mb-2">
              <Sparkles size={12} className="text-blue-400" />
              <span>Try asking</span>
            </div>
            <div className="flex flex-col items-start gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSendMessage(s)}
                  className="text-left text-xs md:text-sm px-3 py-2 rounded-xl glass border border-white/10 text-gray-300 hover:text-white hover:border-blue-500/40 hover:bg-blue-600/10 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex justify-start animate-fade-in pl-4">
            <div className="glass px-4 py-3 rounded-2xl rounded-tl-sm text-gray-400 flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: "0ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: "150ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: "300ms" }}></div>
              <span className="ml-2 text-sm">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 sm:p-6 border-t border-white/5 bg-black/20 backdrop-blur-md">
        <ChatInput onSend={handleSendMessage} disabled={loading} />
      </div>
    </div>
  );
}