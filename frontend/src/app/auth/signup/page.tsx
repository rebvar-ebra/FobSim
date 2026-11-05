"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box, User, Mail, Lock, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { API_URL } from "../../api";

const HOME_REDIRECT_DELAY_MS = 1500;

export default function SignupPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [registered, setRegistered] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        setRegistered(true);
        window.setTimeout(() => {
          router.replace("/");
        }, HOME_REDIRECT_DELAY_MS);
      } else {
        const data = await res.json();
        setError(data.detail || "Signup failed");
      }
    } catch {
      setError("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1021] overflow-hidden relative w-full px-4">
      <div className="absolute top-[-10%] left-[-10%] w-[60%] md:w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[60%] md:w-[40%] h-[40%] bg-violet-600/10 blur-[120px] rounded-full" />

      <div className="w-full max-w-md p-6 md:p-8 relative z-10 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 mb-6 animate-float">
            <Box size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter text-center">Create Account</h1>
          <p className="text-slate-400 text-sm mt-3 font-medium text-center">Join the FobSim Research Community</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative group">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="text"
              placeholder="Full Name"
              required
              disabled={registered}
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium"
              value={formData.full_name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, full_name: e.target.value })}
            />
          </div>

          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="email"
              placeholder="Email Address"
              required
              disabled={registered}
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium"
              value={formData.email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="password"
              placeholder="Password"
              required
              disabled={registered}
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium"
              value={formData.password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {error && <div className="text-red-400 text-xs font-bold py-3 px-4 bg-red-400/10 border border-red-400/20 rounded-xl animate-shake">{error}</div>}

          {registered && (
            <div
              role="status"
              aria-live="polite"
              className="flex items-start gap-3 rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-4 py-3 text-emerald-300"
            >
              <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
              <div>
                <p className="text-sm font-bold">Registration successful</p>
                <p className="mt-0.5 text-xs text-emerald-200/70">Taking you to the home page…</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || registered}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-black text-lg hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group shadow-xl shadow-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-75"
          >
            {loading ? (
              <Loader2 className="animate-spin" />
            ) : registered ? (
              <><CheckCircle2 size={20} /> Account Created</>
            ) : (
              <>Sign Up <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} /></>
            )}
          </button>
        </form>

        <p className="text-center text-slate-500 mt-8 font-medium">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-cyan-400 font-bold hover:text-cyan-300 transition-colors">Log In</Link>
        </p>
      </div>
    </div>
  );
}
