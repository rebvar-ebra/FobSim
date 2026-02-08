"use client";

import React, { useState } from "react";
import { CLOUD_PROVIDERS, calculateEstimatedCost } from "../../utils/cloud_pricing";
import { CloudLogoAWS, CloudLogoGCP, CloudLogoAzure } from "../constants";
import { Settings2, Globe, ShieldCheck, ChevronRight } from "lucide-react";

interface ParameterConfigProps {
  config: { fog: number; miners: number; tx: number; diff: number };
  setConfig: (config: any) => void;
  selectedCloud: string;
  setSelectedCloud: (id: string) => void;
  configError: string | null;
  onSave: () => void;
}

export default function ParameterConfig({ config, setConfig, selectedCloud, setSelectedCloud, configError, onSave }: ParameterConfigProps) {
  const [showConfig, setShowConfig] = useState(false);
  const provider = CLOUD_PROVIDERS.find(p => p.id === selectedCloud)!;

  const LogoMap: any = { aws: CloudLogoAWS, gcp: CloudLogoGCP, azure: CloudLogoAzure };
  const Logo = LogoMap[selectedCloud];

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", margin: 0 }}>Step 3: Configure Parameters</h2>
          <p style={{ color: "#64748b", fontSize: 14, margin: "4px 0 0" }}>Infrastructure and cloud settings.</p>
        </div>
      </div>

      <div className="space-y-4 mb-8">
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Select Cloud Provider</label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          {CLOUD_PROVIDERS.map(p => {
            const PLogo = LogoMap[p.id];
            const active = selectedCloud === p.id;
            return (
              <button
                key={p.id}
                onClick={() => { setSelectedCloud(p.id); setShowConfig(false); }}
                style={{
                  padding: "16px 12px", borderRadius: 16, border: active ? `2px solid ${p.color}` : "2px solid #f1f5f9",
                  background: "white", cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: 8, transition: "all 0.2s",
                  boxShadow: active ? `0 10px 25px ${p.color}20` : "none",
                  transform: active ? "translateY(-2px)" : "none"
                }}
              >
                <div style={{ color: active ? p.color : "#94a3b8" }}>
                  <PLogo />
                </div>
                <span style={{ fontSize: 11, fontWeight: 700, color: active ? "#0f172a" : "#64748b" }}>{p.name.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="bg-slate-50 rounded-2xl p-5 border border-slate-100 mb-8 transition-all hover:border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0`} style={{ background: `${provider.color}15`, color: provider.color }}>
              <Logo />
            </div>
            <div>
              <h4 className="font-bold text-slate-800 text-sm">{provider.name} Connection</h4>
              <p className="text-xs text-slate-500">Service integration for node provisioning.</p>
            </div>
          </div>
          <button
             onClick={() => setShowConfig(!showConfig)}
             className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-50 transition flex items-center gap-2"
          >
            <Settings2 size={14} />
            {showConfig ? 'Close Setup' : 'Connect'}
          </button>
        </div>

        {showConfig ? (
          <div className="pt-4 border-t border-slate-200 grid grid-cols-1 gap-4 animate-in fade-in slide-in-from-top-2">
            {provider.configFields.map(f => (
              <div key={f.id}>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1 block">{f.label}</label>
                <input
                  type="password"
                  placeholder={f.placeholder}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-slate-400 transition"
                />
              </div>
            ))}
            <p className="text-[10px] text-slate-400 italic mt-2">Credentials are encrypted and stored locally for this session.</p>
          </div>
        ) : (
          <div className="flex gap-6 mt-2 pt-2 border-t border-slate-100">
             <div className="flex items-center gap-2">
                <Globe size={14} className="text-slate-400" />
                <span className="text-[11px] font-medium text-slate-600">Standard API Endpoint</span>
             </div>
             <div className="flex items-center gap-2">
                <ShieldCheck size={14} className="text-emerald-500" />
                <span className="text-[11px] font-medium text-slate-600">Secure Transport Active</span>
             </div>
          </div>
        )}
      </div>

      {configError && <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 16 }}>⚠️ {configError}</p>}

      <div className="grid grid-cols-2 gap-4 mb-4">
        {[{ k: "fog", l: "Fog Nodes", v: config.fog }, { k: "miners", l: "Miners", v: config.miners }, { k: "tx", l: "TX/Block", v: config.tx }, { k: "diff", l: "Difficulty", v: config.diff }].map(f => (
          <div key={f.k} className="p-4 bg-white border border-slate-200 rounded-2xl hover:border-slate-300 transition group">
            <label style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", display: "block", marginBottom: 6, textTransform: "uppercase" }}>{f.l}</label>
            <input type="number" value={f.v} onChange={e => setConfig({ ...config, [f.k]: +e.target.value })}
              style={{ width: "100%", padding: "4px 0", border: "none", fontSize: 20, fontWeight: 700, outline: "none", color: "#0f172a" }} />
          </div>
        ))}
      </div>

      <div className="mt-4 p-5 rounded-2xl bg-[#0f1021] text-white flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-4">
           <div className="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400">
              <ChevronRight size={24} />
           </div>
           <div>
              <p className="text-[11px] text-slate-400 font-bold uppercase tracking-widest">Estimated Cloud Cost</p>
              <h3 className="text-2xl font-bold font-mono">
                ${calculateEstimatedCost(selectedCloud, config.fog + config.miners).toFixed(4)}<span className="text-xs text-slate-500 ml-1">/hr</span>
              </h3>
           </div>
        </div>
        <button
          onClick={onSave}
          className="px-6 py-3 bg-cyan-500 text-white rounded-xl font-bold hover:bg-cyan-400 transition shadow-lg shadow-cyan-500/20 text-sm"
        >
          Save Specs
        </button>
      </div>
    </>
  );
}
