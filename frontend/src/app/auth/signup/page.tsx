"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Box, User, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import { API_URL } from "../../api";

export default function SignupPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
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
        router.push("/");
      } else {
        const data = await res.json();
        setError(data.detail || "Signup failed");
      }
    } catch (err) {
      setError("Connection error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1021] overflow-hidden relative">
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-violet-600/10 blur-[120px] rounded-full" />

      <div className="w-full max-w-md p-8 relative z-10">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 mb-4 animate-float">
            <Box size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Create Account</h1>
          <p className="text-slate-400 text-sm mt-2">Join the FobSim Research Community</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="text"
              placeholder="Full Name"
              required
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 text-white placeholder-slate-500 transition-all"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
          </div>

          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="email"
              placeholder="Email Address"
              required
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 text-white placeholder-slate-500 transition-all"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="password"
              placeholder="Password"
              required
              className="w-full bg-slate-800/50 border border-slate-700/50 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 text-white placeholder-slate-500 transition-all"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {error && <p className="text-red-400 text-sm py-2 px-4 bg-red-400/10 rounded-lg">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-bold text-lg hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group"
          >
            {loading ? <Loader2 className="animate-spin" /> : <>Sign Up <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} /></>}
          </button>
        </form>

        <p className="text-center text-slate-500 mt-8">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-cyan-400 font-semibold hover:underline">Log In</Link>
        </p>
      </div>
    </div>
  );
}
