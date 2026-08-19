"use client";

import { useState, FormEvent } from "react";
import { loginBackend } from "@/lib/api";

interface LoginProps {
  onLoginSuccess: (token: string, username: string) => void;
}

export default function Login({ onLoginSuccess }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = await loginBackend(username, password);
      onLoginSuccess(token, username);
    } catch (err: any) {
      setError(err.message || "Failed to login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex w-full max-w-sm flex-col items-center justify-center p-6 glass-panel rounded-2xl animate-fade-in shadow-2xl transition-all duration-300 mx-auto mt-12">
      <h2 className="text-2xl font-bold mb-6 tracking-tight text-white/90">AskLedger Login</h2>
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
      
      <div className="mt-6 text-xs text-gray-500 text-center">
        <p>Demo accounts (password123):</p>
        <p>alice, bob, charlie, admin</p>
      </div>
    </div>
  );
}
