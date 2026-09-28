"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { errorMessage, loginBackend } from "@/lib/api";

interface LoginProps {
  onLoginSuccess: (token: string, username: string) => void;
  autoLogin?: string | null;
  onAutoLoginConsumed?: () => void;
}

const DEMO_ACCOUNTS = [
  { username: "alice", tenant: "Acme Corp" },
  { username: "bob", tenant: "Globex Inc" },
  { username: "charlie", tenant: "Initech LLC" },
];

export default function Login({ onLoginSuccess, autoLogin, onAutoLoginConsumed }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [waking, setWaking] = useState(false);
  const consumedRef = useRef<string | null>(null);

  const doLogin = async (u: string, p: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = await loginBackend(u, p, () => setWaking(true));
      onLoginSuccess(token, u);
    } catch (err) {
      setError(errorMessage(err, "Failed to login"));
    } finally {
      setLoading(false);
      setWaking(false);
    }
  };

  // One-click login triggered from the landing page's demo account cards
  useEffect(() => {
    if (autoLogin && consumedRef.current !== autoLogin) {
      consumedRef.current = autoLogin;
      setUsername(autoLogin);
      doLogin(autoLogin, "password123");
      onAutoLoginConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLogin]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    doLogin(username, password);
  };

  return (
    <div className="mx-auto mt-6 flex w-full max-w-sm flex-col items-center justify-center rounded-xl border border-rule bg-surface p-6 animate-fade-in">
      <h2 className="text-2xl font-bold mb-1 tracking-tight text-ink">AskLedger Login</h2>
      <p className="mb-5 text-center text-xs text-graphite">
        This is a portfolio demo — pick a demo tenant below, or sign in manually.
      </p>

      {/* One-click demo tenants */}
      <div className="w-full grid grid-cols-3 gap-2 mb-5">
        {DEMO_ACCOUNTS.map((acc) => (
          <button
            key={acc.username}
            type="button"
            disabled={loading}
            onClick={() => {
              setUsername(acc.username);
              doLogin(acc.username, "password123");
            }}
            className="group flex flex-col items-center gap-1 rounded-lg border border-rule bg-paper px-2 py-3 transition-colors hover:border-ledger hover:bg-ledger-soft disabled:opacity-50"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ledger-soft font-mono text-sm font-bold text-ledger">
              {acc.username[0].toUpperCase()}
            </span>
            <span className="text-xs font-medium capitalize text-ink">{acc.username}</span>
            <span className="text-center text-[9px] leading-none text-graphite">{acc.tenant}</span>
          </button>
        ))}
      </div>

      <div className="w-full flex items-center gap-3 mb-5">
        <div className="h-px flex-1 bg-rule" />
        <span className="font-mono text-[10px] uppercase tracking-wider text-graphite">or sign in manually</span>
        <div className="h-px flex-1 bg-rule" />
      </div>

      <form onSubmit={handleLogin} className="w-full flex flex-col space-y-4">
        <div>
          <label className="mb-1 ml-1 block font-mono text-[11px] uppercase tracking-wider text-graphite" htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            className="w-full rounded-lg border border-rule bg-paper px-4 py-2 text-sm text-ink transition-colors focus:border-ledger focus:outline-none focus:ring-1 focus:ring-ledger"
            placeholder="e.g. alice, bob, charlie"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label className="mb-1 ml-1 block font-mono text-[11px] uppercase tracking-wider text-graphite" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="w-full rounded-lg border border-rule bg-paper px-4 py-2 text-sm text-ink transition-colors focus:border-ledger focus:outline-none focus:ring-1 focus:ring-ledger"
            placeholder="password123"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>

        {waking && (
          <div className="py-1 text-sm text-ledger">
            Waking up the server. The free hosting sleeps when idle, so this can take up to a minute.
          </div>
        )}
        {error && <div className="py-1 text-sm font-medium text-red-700 dark:text-red-300">{error}</div>}

        <button
          type="submit"
          className="mt-2 flex w-full items-center justify-center rounded-full bg-ink px-4 py-2 font-medium text-paper transition-colors hover:bg-ledger disabled:opacity-50"
          disabled={loading || !username.trim()}
        >
          {loading ? (
             <div className="w-5 h-5 border-2 border-paper/30 border-t-paper rounded-full animate-spin"></div>
          ) : "Login"}
        </button>
      </form>

      <div className="mt-5 text-center text-[10px] leading-relaxed text-graphite">
        Every demo account only sees its own tenant&apos;s data — try two different accounts
        to see the isolation for yourself.
      </div>
    </div>
  );
}
