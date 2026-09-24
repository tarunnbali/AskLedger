"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import { loginBackend } from "@/lib/api";

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
  const consumedRef = useRef<string | null>(null);

  const doLogin = async (u: string, p: string) => {
    setLoading(true);
    setError(null);
    try {
      const token = await loginBackend(u, p);
      onLoginSuccess(token, u);
    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setLoading(false);
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
    <div className="flex w-full max-w-sm flex-col items-center justify-center p-6 glass-panel rounded-2xl animate-fade-in shadow-2xl transition-all duration-300 mx-auto mt-6">
      <h2 className="text-2xl font-bold mb-1 tracking-tight text-white/90">AskLedger Login</h2>
      <p className="text-xs text-gray-500 mb-5 text-center">
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
            className="flex flex-col items-center gap-1 rounded-xl border border-white/10 bg-black/30 hover:bg-blue-600/20 hover:border-blue-500/50 px-2 py-3 transition-all disabled:opacity-50 group"
          >
            <span className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center text-sm font-bold group-hover:scale-110 transition-transform">
              {acc.username[0].toUpperCase()}
            </span>
            <span className="text-xs font-medium text-gray-200 capitalize">{acc.username}</span>
            <span className="text-[9px] text-gray-500 leading-none text-center">{acc.tenant}</span>
          </button>
        ))}
      </div>

      <div className="w-full flex items-center gap-3 mb-5">
        <div className="h-px flex-1 bg-white/10" />
        <span className="text-[10px] uppercase tracking-wider text-gray-600">or sign in manually</span>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <form onSubmit={handleLogin} className="w-full flex flex-col space-y-4">
        <div>
          <label className="block text-xs uppercase tracking-wider text-gray-400 mb-1 ml-1" htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            className="w-full bg-black/40 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm"
            placeholder="e.g. alice, bob, charlie"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-gray-400 mb-1 ml-1" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="w-full bg-black/40 border border-white/10 text-white rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm"
            placeholder="password123"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>

        {error && <div className="text-red-400 text-sm py-1 font-medium">{error}</div>}

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-4 rounded-lg shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-all hover:scale-[1.02] active:scale-[0.98] mt-2 disabled:opacity-50 flex justify-center items-center"
          disabled={loading || !username.trim()}
        >
          {loading ? (
             <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          ) : "Login"}
        </button>
      </form>

      <div className="mt-5 text-[10px] text-gray-600 text-center leading-relaxed">
        Every demo account only sees its own tenant's data — try two different accounts
        to see the isolation for yourself.
      </div>
    </div>
  );
}
