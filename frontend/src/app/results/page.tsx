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
  Box,
  Zap,
  ShieldAlert
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

  const filteredHistory = history.filter((item: any) =>
    item.consensus.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.function.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 md:px-8 pb-12 text-slate-200">
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end mb-8 gap-6 mt-6">
        <div>
          <h1 className="text-2xl md:text-3xl lg:text-4xl font-black text-white flex items-center gap-3 tracking-tighter">
            <div className="w-12 h-12 bg-cyan-500/10 rounded-2xl flex items-center justify-center shrink-0">
              <History className="text-cyan-400" size={28} />
            </div>
            Simulation History
          </h1>
          <p className="text-slate-400 mt-2 text-sm md:text-base font-medium">Review and compare your past blockchain experiments</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          <div className="relative flex-1 sm:min-w-[300px]">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input
              type="text"
              placeholder="Search simulations..."
              className="w-full bg-slate-900/60 border border-slate-800 rounded-2xl py-3.5 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 text-white transition-all text-sm font-bold placeholder:text-slate-600"
              value={searchTerm}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="h-[52px] px-6 bg-slate-900/60 border border-slate-800 rounded-2xl text-slate-400 hover:text-white hover:border-slate-700 transition-all flex items-center justify-center gap-2 font-bold text-sm shrink-0">
            <Filter size={18} />
            <span className="lg:hidden text-xs">Filter</span>
          </button>
        </div>
      </div>

      <div className="bg-slate-900/40 border border-slate-800 rounded-[2.5rem] overflow-hidden backdrop-blur-md shadow-2xl">
        <div className="overflow-x-auto scrollbar-hide">
          <table className="w-full text-left border-collapse min-w-[800px]">
            <thead>
              <tr className="bg-slate-800/20 text-slate-500 text-[10px] font-black uppercase tracking-[0.2em] border-b border-slate-800">
                <th className="px-8 py-6">Simulation</th>
                <th className="px-8 py-6">Consensus</th>
                <th className="px-8 py-6">Status</th>
                <th className="px-8 py-6">Metrics</th>
                <th className="px-8 py-6">Started At</th>
                <th className="px-8 py-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-8 py-20 text-center text-slate-500">
                    <div className="flex flex-col items-center">
                      <RefreshCw className="animate-spin text-cyan-500 mb-4" size={32} />
                      <span className="font-bold text-xs uppercase tracking-widest">Retrieving archives...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-8 py-20 text-center">
                    <div className="max-w-xs mx-auto">
                      <div className="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6">
                        <Search className="text-slate-600" size={24} />
                      </div>
                      <h3 className="text-white font-black tracking-tighter text-lg mb-2">No Simulations Found</h3>
                      <p className="text-slate-500 text-sm font-medium leading-relaxed">Try adjusting your search or start a new experiment to see results here.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredHistory.map((item: any) => (
                  <tr key={item.id} className="hover:bg-cyan-500/[0.02] transition-colors group">
                    <td className="px-8 py-6">
                      <div className="flex flex-col">
                        <span className="font-black text-white text-base tracking-tighter group-hover:text-cyan-400 transition-colors uppercase">{item.function}</span>
                        <span className="text-[10px] font-bold text-slate-500 mt-1 uppercase tracking-widest leading-none">{item.placement} Layer</span>
                        {item.config?.Byzantine_nodes > 0 && (
                          <div className="mt-2 inline-flex items-center gap-1.5 text-[9px] font-black text-rose-400 uppercase tracking-widest px-2 py-0.5 bg-rose-500/10 rounded-full w-fit">
                            <ShieldAlert size={10} /> {item.config.Byzantine_nodes} Adversaries
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-cyan-500/10 text-cyan-400 rounded-xl font-mono text-xs font-black uppercase ring-1 ring-cyan-500/20">
                        {item.consensus}
                      </div>
                    </td>
                    <td className="px-8 py-6 text-sm">
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all ${
                        item.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 group-hover:bg-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-500 border-rose-500/20 group-hover:bg-rose-500/20'
                      }`}>
                        {item.status === 'completed' ? <CheckCircle2 size={12} className="shrink-0" /> : <StopCircle size={12} className="shrink-0" />}
                        {item.status}
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-3 text-[10px] font-bold">
                          <div className="flex items-center gap-1.5 text-amber-500/80 bg-amber-500/5 px-2 py-1 rounded-md min-w-[64px]">
                            <Box size={12} /> {item.blocks_mined} BLK
                          </div>
                          <div className="flex items-center gap-1.5 text-cyan-500/80 bg-cyan-500/5 px-2 py-1 rounded-md min-w-[64px]">
                            <Cpu size={12} /> {item.avg_cpu}% CPU
                          </div>
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] font-black text-emerald-500 bg-emerald-500/5 px-2.5 py-1.5 rounded-lg w-fit">
                          <Zap size={14} /> {item.energy_used} <span className="text-[9px] opacity-60">kWh</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                       <div className="flex flex-col">
                          <span className="text-slate-300 text-xs font-bold font-mono uppercase leading-none">{new Date(item.started_at).toLocaleDateString()}</span>
                          <span className="text-[10px] text-slate-500 font-bold mt-1 uppercase tracking-tight opacity-60 leading-none">{new Date(item.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                       </div>
                    </td>
                    <td className="px-8 py-6 text-right">
                      <button className="w-10 h-10 flex items-center justify-center bg-slate-800/0 hover:bg-cyan-500/10 rounded-xl text-slate-500 hover:text-cyan-400 transition-all ml-auto hover:rotate-12 group/btn">
                        <ExternalLink size={20} className="group-hover/btn:scale-110 transition-transform" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
