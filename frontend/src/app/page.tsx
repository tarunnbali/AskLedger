"use client";

import { useState } from "react";
import {
  MessageSquareText,
  Code2,
  BarChart3,
  ShieldCheck,
  Lock,
  Gauge,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import ChatWidget from "../components/ChatWidget";

const EXAMPLE_QUESTIONS = [
  "What's my total active ARR?",
  "Show me all my cancelled subscriptions",
  "When's my next payment due?",
  "Which subscriptions have a discount?",
  "Show me my pending subscriptions and my next payment date",
];

const DEMO_ACCOUNTS = [
  { username: "alice", tenant: "Acme Corp" },
  { username: "bob", tenant: "Globex Inc" },
  { username: "charlie", tenant: "Initech LLC" },
];

const HOW_IT_WORKS = [
  {
    icon: MessageSquareText,
    title: "Ask in plain English",
    text: "No SQL, no dashboards. Just type a question the way you'd ask a colleague.",
  },
  {
    icon: Code2,
    title: "AI writes secure SQL",
    text: "An LLM translates your question into a validated, read-only query — never INSERT, UPDATE, or DELETE.",
  },
  {
    icon: BarChart3,
    title: "Get a straight answer",
    text: "The query runs against your data and comes back as a plain-English answer, with the SQL and full result table available if you want it.",
  },
];

const TRUST_STRIP = [
  { icon: ShieldCheck, text: "Row-Level Security enforces tenant isolation at the database layer" },
  { icon: Lock, text: "Read-only queries only — DML/DDL is blocked before execution" },
  { icon: Gauge, text: "Rate-limited per visitor to keep the demo fast for everyone" },
];

export default function Home() {
  const [chatOpen, setChatOpen] = useState(false);
  const [demoUser, setDemoUser] = useState<string | null>(null);

  const openWithDemoUser = (username: string) => {
    setDemoUser(username);
    setChatOpen(true);
  };

  return (
    <main className="relative min-h-screen flex flex-col items-center bg-[#121212] overflow-hidden">
      {/* Ambient background: dot grid + soft glow orbs */}
      <div className="absolute inset-0 bg-dot-grid opacity-40 pointer-events-none" />
      <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none animate-float-slow" />
      <div
        className="absolute top-40 -right-32 w-[500px] h-[500px] bg-purple-600/15 rounded-full blur-[120px] pointer-events-none animate-float-slow"
        style={{ animationDelay: "3s" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#121212]/40 to-[#121212] pointer-events-none" />

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative z-10 w-full max-w-4xl flex flex-col items-center justify-center text-center px-4 pt-20 pb-14 animate-fade-in">
        <div className="glass inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs text-gray-300 mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_currentColor]" />
          AI chatbot for subscription billing analytics
        </div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4">
          Ask<span className="gradient-text">Ledger</span>
        </h1>
        <p className="text-gray-400 text-lg md:text-xl max-w-2xl mb-8">
          Ask your subscription and billing data questions in plain English — no SQL,
          no dashboards. AskLedger turns your question into a secure query and answers
          you directly, scoped strictly to your own data.
        </p>

        <button
          onClick={() => setChatOpen(true)}
          className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-7 rounded-xl shadow-[0_0_25px_rgba(59,130,246,0.45)] transition-all hover:scale-[1.03] active:scale-[0.98] mb-10"
        >
          <Sparkles size={18} />
          Try the live demo
          <ArrowRight size={18} />
        </button>

        <div className="glass px-6 py-3 rounded-xl flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs sm:text-sm text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_currentColor]"></div>
            System Online
          </div>
          <div className="hidden sm:block">|</div>
          <div>Next.js · FastAPI · PostgreSQL RLS · Gemini</div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────── */}
      <section className="relative z-10 w-full max-w-5xl px-4 py-14 border-t border-white/5">
        <h2 className="text-center text-sm uppercase tracking-widest text-gray-500 mb-10">
          How it works
        </h2>
        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Connecting flow line (desktop only) */}
          <div className="hidden md:block absolute top-[38px] left-[16.5%] right-[16.5%] h-px bg-gradient-to-r from-blue-500/40 via-purple-500/40 to-blue-500/40" />

          {HOW_IT_WORKS.map((step, i) => (
            <div key={step.title} className="relative glass-panel rounded-2xl p-6 flex flex-col items-start">
              <span className="absolute top-4 right-5 text-4xl font-bold text-white/5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="w-11 h-11 rounded-xl bg-blue-500/15 text-blue-400 flex items-center justify-center mb-4 ring-4 ring-[#121212]">
                <step.icon size={22} />
              </div>
              <h3 className="text-white font-semibold mb-2">{step.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── What can you ask ──────────────────────────────────────────── */}
      <section className="relative z-10 w-full max-w-4xl px-4 py-14 border-t border-white/5">
        <h2 className="text-center text-sm uppercase tracking-widest text-gray-500 mb-8">
          What can you ask?
        </h2>
        <div className="flex flex-wrap justify-center gap-3">
          {EXAMPLE_QUESTIONS.map((q) => (
            <div
              key={q}
              className="glass px-4 py-2.5 rounded-full text-sm text-gray-300 border border-white/10 hover:border-blue-500/30 transition-colors"
            >
              &ldquo;{q}&rdquo;
            </div>
          ))}
        </div>
      </section>

      {/* ── Demo accounts ─────────────────────────────────────────────── */}
      <section className="relative z-10 w-full max-w-4xl px-4 py-14 border-t border-white/5">
        <h2 className="text-center text-sm uppercase tracking-widest text-gray-500 mb-2">
          Try it yourself
        </h2>
        <p className="text-center text-gray-500 text-sm mb-8">
          Three demo tenants, each with their own isolated data. Click one to jump straight in.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {DEMO_ACCOUNTS.map((acc) => (
            <button
              key={acc.username}
              onClick={() => openWithDemoUser(acc.username)}
              className="glass-panel rounded-2xl p-5 text-left hover:border-blue-500/30 hover:-translate-y-1 transition-all group"
            >
              <div className="w-10 h-10 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center text-sm font-bold mb-3 group-hover:scale-110 transition-transform">
                {acc.username[0].toUpperCase()}
              </div>
              <div className="text-white font-medium capitalize flex items-center gap-1.5">
                {acc.username}
                <ArrowRight size={13} className="text-gray-600 group-hover:text-blue-400 group-hover:translate-x-0.5 transition-all" />
              </div>
              <div className="text-xs text-gray-500">{acc.tenant}</div>
            </button>
          ))}
        </div>
      </section>

      {/* ── Trust strip ────────────────────────────────────────────────── */}
      <section className="relative z-10 w-full max-w-4xl px-4 py-14 border-t border-white/5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {TRUST_STRIP.map((item) => (
            <div key={item.text} className="flex flex-col items-center text-center gap-3 px-2">
              <div className="w-10 h-10 rounded-full bg-white/5 text-gray-300 flex items-center justify-center">
                <item.icon size={18} />
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{item.text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="relative z-10 w-full text-center text-gray-600 text-xs py-8 border-t border-white/5">
        <p>Built with Next.js, FastAPI, and PostgreSQL · Portfolio project</p>
      </footer>

      {/* Floating Chat Widget */}
      <ChatWidget
        isOpen={chatOpen}
        onOpenChange={setChatOpen}
        autoLoginUsername={demoUser}
        onAutoLoginConsumed={() => setDemoUser(null)}
      />
    </main>
  );
}
