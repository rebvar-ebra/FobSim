"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import { API_URL } from "../../api";

export default function LoginPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formDataBody = new URLSearchParams();
      formDataBody.append("username", formData.email);
      formDataBody.append("password", formData.password);

      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formDataBody,
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        router.push("/");
      } else {
        setError("Invalid email or password");
      }
    } catch (err) {
      setError("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1021] overflow-hidden relative w-full px-4">
      <div className="absolute top-[-10%] right-[-10%] w-[60%] md:w-[40%] h-[40%] bg-violet-600/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[60%] md:w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full" />

      <div className="w-full max-w-md p-6 md:p-8 relative z-10 bg-slate-900/40 backdrop-blur-xl border border-slate-800 rounded-[2.5rem] shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 mb-6 animate-float">
            <Box size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter">Welcome Back</h1>
          <p className="text-slate-400 text-sm mt-3 font-medium">Sign in to continue your research</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-cyan-400 transition-colors" size={18} />
            <input
              type="email"
              placeholder="Email Address"
              required
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
              className="w-full bg-slate-800/30 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white placeholder-slate-600 transition-all font-medium"
              value={formData.password}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {error && <div className="text-red-400 text-xs font-bold py-3 px-4 bg-red-400/10 border border-red-400/20 rounded-xl animate-shake">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-black text-lg hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group shadow-xl shadow-cyan-500/10"
          >
            {loading ? <Loader2 className="animate-spin" /> : <>Log In <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} /></>}
          </button>
        </form>

        <p className="text-center text-slate-500 mt-8 font-medium">
          Don't have an account?{" "}
          <Link href="/auth/signup" className="text-cyan-400 font-bold hover:text-cyan-300 transition-colors">Sign Up</Link>
        </p>
      </div>
    </div>
  );
}
