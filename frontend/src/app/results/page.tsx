"use client";

import { useState, useEffect } from "react";
import {
  History,
  Search,
  Filter,
  ExternalLink,
  CheckCircle2,
  StopCircle,
  RefreshCw,
  Cpu,
  Box
} from "lucide-react";
import { API_URL } from "../api";

export default function ResultsPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/auth/login";
      return;
    }

    fetch(`${API_URL}/api/simulations`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => {
        setHistory(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filteredHistory = history.filter(item =>
    item.consensus.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.function.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <History className="text-cyan-400" size={32} />
            Simulation History
          </h1>
          <p className="text-slate-400 mt-2">Review and compare your past blockchain experiments</p>
        </div>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="text"
              placeholder="Search simulations..."
              className="bg-slate-800/50 border border-slate-700/50 rounded-xl py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 text-white transition-all w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="p-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-400 hover:text-white transition-colors">
            <Filter size={20} />
          </button>
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-3xl overflow-hidden backdrop-blur-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-800/30 text-slate-400 text-xs font-bold uppercase tracking-wider">
              <th className="px-6 py-4">Simulation</th>
              <th className="px-6 py-4">Consensus</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Metrics</th>
              <th className="px-6 py-4">Started At</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                  <RefreshCw className="animate-spin mx-auto mb-2" size={24} />
                  Loading history...
                </td>
              </tr>
            ) : filteredHistory.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                  No simulations found. Start one to see it here!
                </td>
              </tr>
            ) : (
              filteredHistory.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/20 transition-colors group">
                  <td className="px-6 py-5">
                    <p className="font-bold text-white">{item.function}</p>
                    <p className="text-xs text-slate-500">{item.placement} Layer</p>
                  </td>
                  <td className="px-6 py-5 underline text-cyan-400">
                    {item.consensus}
                  </td>
                  <td className="px-6 py-5">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                      item.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                    }`}>
                      {item.status === 'completed' ? <CheckCircle2 size={12} /> : <StopCircle size={12} />}
                      {item.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-4 text-xs font-mono">
                      <div className="flex items-center gap-1 text-amber-400">
                        <Box size={14} /> {item.blocks_mined}
                      </div>
                      <div className="flex items-center gap-1 text-cyan-400">
                        <Cpu size={14} /> {item.avg_cpu}%
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-slate-400 text-sm">
                    {new Date(item.started_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-5 text-right">
                    <button className="p-2 text-slate-500 hover:text-cyan-400 transition-colors">
                      <ExternalLink size={18} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
