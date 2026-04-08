"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Play,
  History,
  BarChart3,
  Activity,
  ShieldCheck,
  Cpu,
  Layers,
  ArrowRight,
  Target,
  Box
} from "lucide-react";
import { API_URL } from "./api";

export default function OverviewPage() {
  const [stats, setStats] = useState({
    totalRuns: 0,
    topAlgorithm: "N/A",
    avgEfficiency: 0,
    activeSimulations: 0
  });

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      // Fetch simulations to compute stats
      fetch(`${API_URL}/api/simulations`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const counts: any = {};
          data.forEach(s => { counts[s.consensus] = (counts[s.consensus] || 0) + 1 });
          const top = Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b);

          setStats({
            totalRuns: data.length,
            topAlgorithm: top,
            avgEfficiency: Math.round(data.reduce((acc, s) => acc + s.avg_cpu, 0) / data.length),
            activeSimulations: data.filter(s => s.status === 'running').length
          });
        }
      });
    }
  }, []);

  const cards = [
    { title: "Total Experiments", value: stats.totalRuns, icon: <Activity className="text-cyan-400" size={24} />, sub: "Past simulations" },
    { title: "Most Used", value: stats.topAlgorithm, icon: <ShieldCheck className="text-violet-400" size={24} />, sub: "Consensus preference" },
    { title: "Avg. CPU Load", value: `${stats.avgEfficiency}%`, icon: <Cpu className="text-emerald-400" size={24} />, sub: "System performance" },
    { title: "Active Nodes", value: stats.activeSimulations, icon: <Layers className="text-amber-400" size={24} />, sub: "Live instances" },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-8 md:space-y-12 pb-20 w-full px-4 lg:px-8">
      <div className="relative p-6 md:p-12 lg:p-16 rounded-[2.5rem] bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/10 blur-[100px] rounded-full translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-violet-600/10 blur-[80px] rounded-full -translate-x-1/2 translate-y-1/2" />

        <div className="relative z-10 max-w-2xl text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold uppercase tracking-widest mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            V2.0 Live Analysis
          </div>
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-black text-white leading-[1.1] tracking-tighter">
            Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-violet-500">FobSim Platform</span>
          </h1>
          <p className="text-slate-400 text-base md:text-xl mt-6 leading-relaxed font-medium">
            The next generation of blockchain simulation. Configure, execute, and analyze complex networking architectures with research-grade precision.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 mt-10">
            <Link
              href="/simulate"
              className="group px-8 py-5 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-black text-lg flex items-center justify-center gap-3 hover:scale-105 transition shadow-2xl shadow-cyan-500/30"
            >
              <Play size={20} fill="currentColor" className="group-hover:translate-x-0.5 transition" /> Start Simulation
            </Link>
            <Link
              href="/results"
              className="px-8 py-5 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl text-slate-300 font-bold hover:bg-slate-700 transition flex items-center justify-center text-lg"
            >
              View History
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {cards.map((card, i) => (
          <div key={i} className="p-6 md:p-8 rounded-[2rem] bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition group flex flex-col items-center text-center backdrop-blur-md">
            <div className="w-14 h-14 rounded-2xl bg-slate-800/80 flex items-center justify-center mb-6 group-hover:scale-110 transition duration-500 group-hover:rotate-3 shadow-xl">
              {card.icon}
            </div>
            <p className="text-slate-500 text-xs font-black uppercase tracking-widest">{card.title}</p>
            <h2 className="text-3xl font-black text-white mt-2 tracking-tighter">{card.value}</h2>
            <p className="text-[10px] font-bold text-slate-600 mt-3 uppercase tracking-wider">{card.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 p-6 md:p-10 rounded-[3rem] bg-slate-900/40 border border-slate-800 backdrop-blur-md">
          <h3 className="text-xl font-black text-white mb-8 flex items-center gap-3 tracking-tighter">
            <div className="w-10 h-10 bg-cyan-500/10 rounded-xl flex items-center justify-center">
              <Activity className="text-cyan-400" size={20} />
            </div>
            Platform Quick Actions
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { title: "Run Benchmark", desc: "Test system limits", icon: <Target className="text-amber-400" />, href: "/simulate" },
              { title: "Analytics Report", desc: "Visual comparison", icon: <BarChart3 className="text-violet-400" />, href: "/analytics" },
              { title: "Review History", desc: "Past experiment logs", icon: <History className="text-emerald-400" />, href: "/results" },
              { title: "System Health", desc: "Resource monitoring", icon: <Cpu className="text-cyan-400" />, href: "/simulate" },
            ].map(item => (
              <Link key={item.title} href={item.href} className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:border-cyan-500/30 hover:bg-slate-800/50 transition flex items-center gap-4 group">
                <div className="w-12 h-12 rounded-2xl bg-slate-700/50 flex items-center justify-center shrink-0">
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-black text-white group-hover:text-cyan-400 transition truncate">{item.title}</h4>
                  <p className="text-xs text-slate-500 font-medium truncate">{item.desc}</p>
                </div>
                <ArrowRight size={18} className="text-slate-600 group-hover:text-white transition group-hover:translate-x-1 shrink-0" />
              </Link>
            ))}
          </div>
        </div>

        <div className="p-8 md:p-10 rounded-[3rem] bg-gradient-to-br from-violet-600/10 via-slate-900/40 to-slate-900/40 border border-violet-500/20 flex flex-col items-center justify-center text-center backdrop-blur-md">
           <div className="p-6 bg-violet-500/10 rounded-full mb-8 relative">
              <Box size={48} className="text-violet-500 animate-float" />
              <div className="absolute inset-0 bg-violet-500 blur-2xl opacity-20" />
           </div>
           <h3 className="text-2xl font-black text-white mb-3 tracking-tighter">Ready for Analysis?</h3>
           <p className="text-slate-400 text-sm mb-8 font-medium leading-relaxed">Compare consensus reliability and throughput across your entire history with deep metrics.</p>
           <Link href="/analytics" className="w-full py-4 bg-violet-600 text-white rounded-2xl font-black text-lg hover:bg-violet-500 transition shadow-xl shadow-violet-600/20 active:scale-95">
              Open Analytics
           </Link>
        </div>
      </div>
    </div>
  );
}
