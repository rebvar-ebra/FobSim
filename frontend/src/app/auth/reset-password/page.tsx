"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Box,
  CheckCircle2,
  Loader2,
  Lock,
} from "lucide-react";
import { API_URL } from "../../api";

const LOGIN_REDIRECT_DELAY_MS = 1500;

function ResetPasswordForm() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    setToken(fragment.get("token"));
    window.history.replaceState(
      window.history.state,
      "",
      `${window.location.pathname}${window.location.search}`,
    );
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");

    if (!token) {
      return;
    }
    if (password !== confirmation) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "This reset link is invalid or expired.");
        return;
      }

      setSuccess(data.message || "Password updated successfully");
      window.setTimeout(() => {
        router.replace("/auth/login");
      }, LOGIN_REDIRECT_DELAY_MS);
    } catch {
      setError("Connection error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (token === undefined) {
    return <main className="min-h-screen bg-[#0f1021]" />;
  }

  if (!token) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-[#0f1021] relative w-full px-4">
        <section className="w-full max-w-md p-6 md:p-8 relative z-10 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] shadow-2xl text-center">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 mb-6">
            <Box size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter">
            Reset link unavailable
          </h1>
          <div role="alert" className="mt-6 text-red-400 text-sm font-bold py-3 px-4 bg-red-400/10 border border-red-400/20 rounded-xl">
            This reset link is missing or invalid.
          </div>
          <Link href="/auth/forgot-password" className="mt-6 flex items-center justify-center rounded-2xl bg-gradient-to-r from-cyan-500 to-violet-600 py-4 text-white font-black transition-all hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60">
            Request another link
          </Link>
          <Link href="/auth/login" className="mt-6 flex items-center justify-center gap-2 text-sm font-bold text-cyan-400 transition-colors hover:text-cyan-300">
            <ArrowLeft size={16} /> Back to login
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-[#0f1021] overflow-hidden relative w-full px-4">
      <div className="absolute top-[-10%] right-[-10%] w-[60%] md:w-[40%] h-[40%] bg-violet-600/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[60%] md:w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full" />

      <section className="w-full max-w-md p-6 md:p-8 relative z-10 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 mb-6 animate-float">
            <Box size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter text-center">
            Choose a new password
          </h1>
          <p className="text-slate-400 text-sm mt-3 font-medium text-center">
            Use at least 6 characters.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="password"
              placeholder="New Password"
              autoComplete="new-password"
              minLength={6}
              required
              disabled={Boolean(success)}
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium disabled:opacity-70"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="password"
              placeholder="Confirm New Password"
              autoComplete="new-password"
              minLength={6}
              required
              disabled={Boolean(success)}
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium disabled:opacity-70"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          </div>

          {error && (
            <div role="alert" className="text-red-400 text-xs font-bold py-3 px-4 bg-red-400/10 border border-red-400/20 rounded-xl">
              {error}
            </div>
          )}

          {success && (
            <div role="status" aria-live="polite" className="flex items-start gap-3 rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-4 py-3 text-emerald-300">
              <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
              <div>
                <p className="text-sm font-bold">{success}</p>
                <p className="mt-0.5 text-xs text-emerald-200/70">Taking you back to login…</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || Boolean(success)}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-black text-lg hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl shadow-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-75"
          >
            {loading ? (
              <Loader2 className="animate-spin" />
            ) : success ? (
              <><CheckCircle2 size={20} /> Password updated</>
            ) : (
              <>Save new password</>
            )}
          </button>
        </form>

        <Link href="/auth/login" className="mt-8 flex items-center justify-center gap-2 text-sm font-bold text-cyan-400 transition-colors hover:text-cyan-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 rounded">
          <ArrowLeft size={16} /> Back to login
        </Link>
      </section>
    </main>
  );
}

export default function ResetPasswordPage() {
  return <ResetPasswordForm />;
}
