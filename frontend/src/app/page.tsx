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
    <div className="max-w-7xl mx-auto space-y-12 pb-20 w-full px-4 lg:px-8">
      <div className="relative p-8 md:p-12 rounded-[2.5rem] bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/10 blur-[100px] rounded-full translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-violet-600/10 blur-[80px] rounded-full -translate-x-1/2 translate-y-1/2" />

        <div className="relative z-10 max-w-2xl">
          <h1 className="text-4xl md:text-5xl font-extrabold text-white leading-tight">
            Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-violet-500">FobSim Platform</span>
          </h1>
          <p className="text-slate-400 text-lg md:text-xl mt-6 leading-relaxed">
            The next generation of blockchain simulation. Configure, execute, and analyze complex networking architectures with research-grade precision.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 mt-10">
            <Link
              href="/simulate"
              className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-2xl text-white font-bold flex items-center justify-center gap-2 hover:scale-105 transition shadow-lg shadow-cyan-500/20"
            >
              <Play size={20} fill="currentColor" /> Start New Simulation
            </Link>
            <Link
              href="/results"
              className="px-8 py-4 bg-slate-800 border border-slate-700 rounded-2xl text-slate-300 font-bold hover:bg-slate-700 transition flex items-center justify-center"
            >
              View History
            </Link>
          </div>
        </div>
      </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards.map((card, i) => (
              <div key={i} className="p-6 rounded-[2rem] bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition group flex flex-col items-center text-center">
                <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center mb-4 group-hover:scale-110 transition duration-300 flex-shrink-0">
                  {card.icon}
                </div>
                <p className="text-slate-500 text-sm font-medium">{card.title}</p>
                <h2 className="text-2xl font-bold text-white mt-1">{card.value}</h2>
                <p className="text-xs text-slate-500 mt-2">{card.sub}</p>
              </div>
            ))}
          </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 p-8 rounded-[2rem] bg-slate-900/40 border border-slate-800">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Activity className="text-cyan-400" size={20} /> Platform Quick Actions
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { title: "Run Benchmark", desc: "Test system limits", icon: <Target className="text-amber-400" />, href: "/simulate" },
              { title: "Analytics Report", desc: "Visual comparison", icon: <BarChart3 className="text-violet-400" />, href: "/analytics" },
              { title: "Review History", desc: "Past experiment logs", icon: <History className="text-emerald-400" />, href: "/results" },
              { title: "System Health", desc: "Resource monitoring", icon: <Cpu className="text-cyan-400" />, href: "/simulate" },
            ].map(item => (
              <Link key={item.title} href={item.href} className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:border-cyan-500/30 hover:bg-slate-800/50 transition flex items-center gap-4 group">
                <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center">
                  {item.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-white group-hover:text-cyan-400 transition">{item.title}</h4>
                  <p className="text-xs text-slate-500">{item.desc}</p>
                </div>
                <ArrowRight size={16} className="text-slate-600 group-hover:text-white transition group-hover:translate-x-1" />
              </Link>
            ))}
          </div>
        </div>

        <div className="p-8 rounded-[2.5rem] bg-gradient-to-br from-violet-600/10 to-transparent border border-violet-500/20 flex flex-col items-center justify-center text-center">
           <Box size={64} className="text-violet-500 opacity-40 mb-6 animate-float" />
           <h3 className="text-xl font-bold text-white mb-2">Ready for Analysis?</h3>
           <p className="text-slate-400 text-sm mb-6">Compare consensus reliability and throughput across your entire history.</p>
           <Link href="/analytics" className="w-full py-3 bg-violet-600 text-white rounded-xl font-bold hover:bg-violet-500 transition">
              Open Analytics
           </Link>
        </div>
      </div>
    </div>
  );
}
