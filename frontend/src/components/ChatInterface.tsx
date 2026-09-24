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

interface ChatInterfaceProps {
  token: string;
  // A question picked on the landing page, sent automatically once ready
  initialQuestion?: string | null;
  onInitialQuestionSent?: () => void;
}

export default function ChatInterface({ token, initialQuestion, onInitialQuestionSent }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hi! I'm AskLedger — ask me anything about your subscriptions, billing, or revenue in plain English, and I'll turn it into a secure query and answer you directly. You'll only ever see your own tenant's data.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [waking, setWaking] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Send a question picked on the landing page, waiting for any in-flight request
  const sentInitialRef = useRef<string | null>(null);
  useEffect(() => {
    if (!initialQuestion) {
      sentInitialRef.current = null;
    } else if (!loading && sentInitialRef.current !== initialQuestion) {
      // The ref guards against React Strict Mode running this effect twice
      sentInitialRef.current = initialQuestion;
      onInitialQuestionSent?.();
      handleSendMessage(initialQuestion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion, loading]);

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
      const response = await queryBackend(query, token, history, () => setWaking(true));

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
      setWaking(false);
    }
  };

  return (
    <div className="mb-4 mt-4 flex h-full w-full flex-col overflow-hidden rounded-xl border border-rule bg-paper-2/40">
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
            <div className="mb-2 flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-graphite">
              <Sparkles size={12} className="text-ledger" />
              <span>Try asking</span>
            </div>
            <div className="flex flex-col items-start gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSendMessage(s)}
                  className="rounded-lg border border-rule bg-surface px-3 py-2 text-left text-xs text-ink transition-colors hover:border-ledger hover:text-ledger md:text-sm"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex justify-start animate-fade-in pl-4">
            <div className="flex items-center space-x-2 rounded-2xl rounded-tl-sm border border-rule bg-surface px-4 py-3 text-graphite">
              <div className="w-2 h-2 rounded-full bg-ledger animate-bounce" style={{ animationDelay: "0ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-ledger animate-bounce" style={{ animationDelay: "150ms" }}></div>
              <div className="w-2 h-2 rounded-full bg-ledger animate-bounce" style={{ animationDelay: "300ms" }}></div>
              <span className="ml-2 text-sm">{waking ? "Waking up the server, this can take a minute..." : "Thinking..."}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-rule p-4 sm:p-6">
        <ChatInput onSend={handleSendMessage} disabled={loading} />
      </div>
    </div>
  );
}