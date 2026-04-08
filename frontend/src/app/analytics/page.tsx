"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Cell
} from "recharts";
import { BarChart3, TrendingUp, Cpu, Box, Info, Target, Zap, GitFork } from "lucide-react";
import { API_URL } from "../api";

export default function AnalyticsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/auth/login";
      return;
    }

    fetch(`${API_URL}/api/analytics/compare`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(d => {
        setData(Array.isArray(d) ? d : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const COLORS = ['#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#6366f1'];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12 text-slate-200">
      <div className="flex flex-col md:flex-row md:justify-between md:items-end mb-10 gap-4 mt-6">
        <div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-black text-white flex items-center gap-3 tracking-tighter">
            <div className="w-12 h-12 bg-cyan-500/10 rounded-2xl flex items-center justify-center">
              <BarChart3 className="text-cyan-400" size={28} />
            </div>
            Consensus Analysis
          </h1>
          <p className="text-slate-400 mt-2 text-sm md:text-base font-medium">Side-by-side performance comparison of blockchain algorithms</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-80">
          <div className="relative">
            <TrendingUp className="animate-pulse text-cyan-400" size={48} />
            <div className="absolute inset-0 bg-cyan-400 blur-xl opacity-20 animate-pulse" />
          </div>
        </div>
      ) : data.length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 p-10 md:p-20 rounded-[3rem] text-center backdrop-blur-md">
          <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Info className="text-slate-500" size={32} />
          </div>
          <h2 className="text-2xl font-bold text-white mb-3">No Simulation Data Yet</h2>
          <p className="text-slate-400 max-w-md mx-auto leading-relaxed">Run a few simulations with different algorithms to see deep analysis and benchmarks here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
          {/* Card 1: Throughput (TPS) */}
          <div className="bg-slate-900/40 border border-slate-800 p-6 md:p-8 rounded-[2.5rem] backdrop-blur-sm relative overflow-hidden group hover:border-amber-500/30 transition-all">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
              <Zap size={100} className="text-amber-400" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-white mb-8 flex items-center gap-3">
              <div className="w-8 h-8 bg-amber-400/10 rounded-lg flex items-center justify-center">
                <Zap className="text-amber-400" size={16} />
              </div> 
              Transaction Throughput (TPS)
            </h3>
            <div className="h-72 md:h-80 w-full font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={10} tick={{fill: '#475569'}} axisLine={false} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}
                    itemStyle={{ color: '#fff' }}
                    cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  />
                  <Bar dataKey="throughput" radius={[6, 6, 0, 0]} barSize={40}>
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 2: Block Latency */}
          <div className="bg-slate-900/40 border border-slate-800 p-6 md:p-8 rounded-[2.5rem] backdrop-blur-sm relative overflow-hidden group hover:border-cyan-500/30 transition-all">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
              <Box size={100} className="text-cyan-400" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-white mb-8 flex items-center gap-3">
              <div className="w-8 h-8 bg-cyan-400/10 rounded-lg flex items-center justify-center">
                <Box className="text-cyan-400" size={16} />
              </div>
              Block Latency (avg sec/block)
            </h3>
            <div className="h-72 md:h-80 w-full font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={10} axisLine={false} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#06b6d4"
                    strokeWidth={4}
                    dot={{ fill: '#06b6d4', r: 6, strokeWidth: 2, stroke: '#0f172a' }}
                    activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 3: Network Stability (Forks) */}
          <div className="bg-slate-900/40 border border-slate-800 p-6 md:p-8 rounded-[2.5rem] backdrop-blur-sm relative overflow-hidden group hover:border-rose-500/30 transition-all">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
              <GitFork size={100} className="text-rose-400" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-white mb-8 flex items-center gap-3">
              <div className="w-8 h-8 bg-rose-400/10 rounded-lg flex items-center justify-center">
                <GitFork className="text-rose-400" size={16} />
              </div>
              Network Stability (Avg Forks)
            </h3>
            <div className="h-72 md:h-80 w-full font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={10} axisLine={false} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="forks" radius={[6, 6, 0, 0]} barSize={40}>
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 4: Network Integrity */}
          <div className="bg-slate-900/40 border border-slate-800 p-6 md:p-8 rounded-[2.5rem] backdrop-blur-sm relative overflow-hidden group hover:border-emerald-500/30 transition-all">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
              <Target size={100} className="text-emerald-400" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-white mb-8 flex items-center gap-3">
              <div className="w-8 h-8 bg-emerald-400/10 rounded-lg flex items-center justify-center">
                <Target className="text-emerald-400" size={16} />
              </div>
              Network Consistency (%)
            </h3>
            <div className="h-72 md:h-80 w-full font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={10} axisLine={false} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} axisLine={false} tickLine={false} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="consistency"
                    stroke="#10b981"
                    strokeWidth={4}
                    dot={{ fill: '#10b981', r: 6, strokeWidth: 2, stroke: '#0f172a' }}
                    activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 5: Energy Consumption */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 p-6 md:p-8 rounded-[2.5rem] backdrop-blur-sm relative overflow-hidden group hover:border-emerald-500/30 transition-all">
            <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
              <Zap size={120} className="text-emerald-400" />
            </div>
            <h3 className="text-lg md:text-xl font-bold text-white mb-8 flex items-center gap-3">
              <div className="w-8 h-8 bg-emerald-400/10 rounded-lg flex items-center justify-center">
                <Zap className="text-emerald-400" size={16} />
              </div>
              Energy Consumption (Estimated kWh)
            </h3>
            <div className="h-72 md:h-80 w-full font-mono">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="name" stroke="#475569" fontSize={10} axisLine={false} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={12} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="energy" radius={[8, 8, 0, 0]} barSize={60}>
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.energy > 0.1 ? '#f87171' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detailed Insights */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 p-6 md:p-10 rounded-[3rem] backdrop-blur-sm">
            <h3 className="text-lg md:text-xl font-bold text-white mb-10 flex items-center gap-3">
              <TrendingUp className="text-violet-400" size={24} /> 
              Comparative Performance Benchmark
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.map((item, idx) => (
                <div key={item.name} className="p-6 bg-slate-800/30 rounded-[2rem] border border-slate-700/50 hover:border-cyan-500/30 transition-all group">
                  <div className="flex items-center justify-between mb-6">
                    <span className="text-sm font-black text-white uppercase tracking-tighter">{item.name}</span>
                    <span className="text-[10px] px-3 py-1 bg-cyan-500/10 text-cyan-400 rounded-full font-bold uppercase tracking-widest">{item.runs} Runs</span>
                  </div>

                  <div className="grid grid-cols-1 gap-3 mb-6">
                    <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-700/30">
                        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-1">CO2 Footprint</div>
                        <div className={`text-xl font-black ${item.energy > 0.1 ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {(item.energy * 0.4).toFixed(4)} <span className="text-xs opacity-60">kg</span>
                        </div>
                    </div>
                  </div>

                  <div className="space-y-5">
                    <div>
                      <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest mb-2">
                        <span className="text-slate-500">Stability</span>
                        <span className="text-white">{item.consistency}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full overflow-hidden p-0.5">
                        <div
                          className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
                          style={{ width: `${item.consistency}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest mb-2">
                        <span className="text-slate-500">Overhead</span>
                        <span className="text-white">{item.cpu}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 h-2 rounded-full overflow-hidden p-0.5">
                        <div
                          className="bg-gradient-to-r from-orange-500 to-rose-500 h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(249,115,22,0.3)]"
                          style={{ width: `${Math.min(item.cpu, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
