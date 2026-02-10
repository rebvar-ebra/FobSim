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
    <div className="max-w-6xl mx-auto pb-12 text-slate-200">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="text-cyan-400" size={32} />
            Consensus Analysis
          </h1>
          <p className="text-slate-400 mt-2">Side-by-side performance comparison of blockchain algorithms</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <TrendingUp className="animate-pulse text-cyan-400" size={48} />
        </div>
      ) : data.length === 0 ? (
        <div className="bg-slate-900/50 border border-slate-800 p-12 rounded-3xl text-center">
          <Info className="mx-auto mb-4 text-slate-500" size={48} />
          <h2 className="text-xl font-bold text-white mb-2">Not Enough Data</h2>
          <p className="text-slate-400">Run a few simulations with different algorithms to see comparisons here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card 1: Throughput (TPS) */}
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Zap size={80} className="text-amber-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Zap className="text-amber-400" size={20} /> Transaction Throughput (TPS)
            </h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tick={{fill: '#64748b'}} />
                  <YAxis stroke="#64748b" fontSize={12} label={{ value: 'TX / Sec', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="throughput" radius={[4, 4, 0, 0]}>
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 2: Block Latency */}
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Box size={80} className="text-cyan-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Box className="text-cyan-400" size={20} /> Block Latency (avg sec/block)
            </h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={12} label={{ value: 'Seconds', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="latency"
                    stroke="#06b6d4"
                    strokeWidth={3}
                    dot={{ fill: '#06b6d4', r: 6 }}
                    activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 3: Network Stability (Forks) */}
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <GitFork size={80} className="text-rose-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <GitFork className="text-rose-400" size={20} /> Network Stability (Avg Forks)
            </h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} tick={{fill: '#64748b'}} />
                  <YAxis stroke="#64748b" fontSize={12} label={{ value: 'Forks', angle: -90, position: 'insideLeft', fill: '#64748b' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="forks" radius={[4, 4, 0, 0]}>
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 4: Network Integrity */}
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-3xl backdrop-blur-sm relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Target size={80} className="text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Target className="text-emerald-400" size={20} /> Network Consistency (%)
            </h3>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="consistency"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ fill: '#10b981', r: 6 }}
                    activeDot={{ r: 8, stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Card 3: Detailed Insights */}
          <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 p-8 rounded-3xl backdrop-blur-sm">
            <h3 className="text-xl font-bold text-white mb-8 flex items-center gap-2">
              <TrendingUp className="text-violet-400" size={20} /> Comparative Performance Benchmark
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {data.map((item, idx) => (
                <div key={item.name} className="p-6 bg-slate-800/40 rounded-2xl border border-slate-700/50 hover:border-cyan-500/30 transition-all">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-bold text-slate-400 uppercase tracking-widest leading-tight">{item.name}</span>
                    <span className="text-[10px] px-2 py-1 bg-cyan-500/10 text-cyan-400 rounded-md font-mono whitespace-nowrap">{item.runs} Runs</span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-700/30">
                        <div className="text-[10px] text-slate-500 uppercase">Throughput</div>
                        <div className="text-sm font-bold text-cyan-400">{item.throughput} TPS</div>
                    </div>
                    <div className="bg-slate-900/50 p-3 rounded-xl border border-slate-700/30">
                        <div className="text-[10px] text-slate-500 uppercase">Latency</div>
                        <div className="text-sm font-bold text-rose-400">{item.latency}s</div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-500">Network Consistency</span>
                        <span className="text-white">{item.consistency}%</span>
                      </div>
                      <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-full transition-all duration-500"
                          style={{ width: `${item.consistency}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-500">CPU Overhead</span>
                        <span className="text-white">{item.cpu}%</span>
                      </div>
                      <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-orange-500 to-rose-500 h-full transition-all duration-500"
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
