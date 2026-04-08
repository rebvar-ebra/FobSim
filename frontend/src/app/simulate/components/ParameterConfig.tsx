"use client";

import React, { useState } from "react";
import { CLOUD_PROVIDERS, calculateEstimatedCost } from "../../utils/cloud_pricing";
import { CloudLogoAWS, CloudLogoGCP, CloudLogoAzure } from "../constants";
import { Settings2, Globe, ShieldCheck, ChevronRight, Layers } from "lucide-react";

interface ParameterConfigProps {
  config: { fog: number; miners: number; tx: number; diff: number; byzantine: number; attackType: number; layer2Enabled: boolean; layer2BatchSize: number };
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
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-900 m-0">Step 3: Configure Parameters</h2>
          <p className="text-slate-500 text-sm mt-1">Infrastructure and cloud settings.</p>
        </div>
      </div>

      <div className="space-y-4 mb-10">
        <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select Cloud Provider</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 md:gap-4">
          {CLOUD_PROVIDERS.map(p => {
            const PLogo = LogoMap[p.id];
            const active = selectedCloud === p.id;
            return (
              <button
                key={p.id}
                onClick={() => { setSelectedCloud(p.id); setShowConfig(false); }}
                className={`
                  p-4 md:p-6 rounded-2xl border-2 transition-all duration-200 flex flex-col items-center gap-3
                  ${active 
                    ? `border-[${p.color}] bg-white shadow-xl translate-y-[-2px]` 
                    : "border-slate-100 bg-slate-50/50 hover:bg-white hover:border-slate-200"}
                `}
                style={active ? { borderColor: p.color, boxShadow: `0 10px 25px ${p.color}20` } : {}}
              >
                <div className={`transition-colors ${active ? "" : "text-slate-400"}`} style={active ? { color: p.color } : {}}>
                  <PLogo />
                </div>
                <span className={`text-xs font-bold ${active ? "text-slate-900" : "text-slate-500"}`}>
                  {p.name.split(' ')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="bg-slate-50 rounded-[2rem] p-6 border border-slate-100 mb-10 transition-all hover:border-slate-200">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <div className="flex items-center gap-4">
            <div 
              className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
              style={{ background: `${provider.color}15`, color: provider.color }}
            >
              <Logo />
            </div>
            <div>
              <h4 className="font-bold text-slate-800 text-sm md:text-base">{provider.name} Connection</h4>
              <p className="text-xs text-slate-500 mt-0.5">Service integration for node provisioning.</p>
            </div>
          </div>
          <button
             onClick={() => setShowConfig(!showConfig)}
             className="w-full sm:w-auto px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 transition-all shadow-sm flex items-center justify-center gap-2"
          >
            <Settings2 size={14} />
            {showConfig ? 'Close Setup' : 'Configure Integration'}
          </button>
        </div>

        {showConfig ? (
          <div className="pt-6 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in slide-in-from-top-2">
            {provider.configFields.map(f => (
              <div key={f.id}>
                <label className="text-[10px] font-bold text-slate-400 uppercase mb-1.5 block tracking-wider">{f.label}</label>
                <input
                  type="password"
                  placeholder={f.placeholder}
                  className="w-full bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-slate-400 transition-all shadow-sm"
                />
              </div>
            ))}
            <p className="text-[10px] text-slate-400 italic mt-2 md:col-span-2">Credentials are encrypted and stored locally for this session.</p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-6 mt-2 pt-4 border-t border-slate-200/50">
             <div className="flex items-center gap-2">
                <Globe size={14} className="text-slate-400" />
                <span className="text-[11px] font-semibold text-slate-600">Standard API Endpoint</span>
             </div>
             <div className="flex items-center gap-2">
                <ShieldCheck size={14} className="text-emerald-500" />
                <span className="text-[11px] font-semibold text-slate-600">Secure Transport Active</span>
             </div>
          </div>
        )}
      </div>

      {configError && <p className="text-rose-500 text-sm mb-6 flex items-center gap-2">⚠️ {configError}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
        {[
          { k: "fog", l: "Fog Nodes", v: config.fog }, 
          { k: "miners", l: "Miners", v: config.miners }, 
          { k: "tx", l: "TX/Block", v: config.tx }, 
          { k: "diff", l: "Difficulty", v: config.diff }
        ].map(f => (
          <div key={f.k} className="p-5 bg-white border border-slate-100 rounded-2xl hover:border-slate-300 transition-all group shadow-sm bg-gradient-to-br from-white to-slate-50/30">
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">{f.l}</label>
            <input 
              type="number" 
              value={f.v} 
              onChange={e => setConfig({ ...config, [f.k]: +e.target.value })}
              className="w-full bg-transparent border-none text-2xl font-bold outline-none text-slate-900 p-0"
            />
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
          <Layers size={18} className="text-indigo-500" />
        </div>
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Layer 2 Scaling (Rollups)</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        <div className="p-5 bg-white border border-indigo-50 rounded-[1.5rem] hover:border-indigo-100 transition-all flex items-center justify-between shadow-sm">
          <div>
            <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-1">Enable Rollups</label>
            <span className="text-sm font-bold text-indigo-800">{config.layer2Enabled ? "Active" : "Disabled"}</span>
          </div>
          <button 
            onClick={() => setConfig({ ...config, layer2Enabled: !config.layer2Enabled })}
            className={`w-14 h-7 rounded-full flex items-center transition-all duration-300 px-1
              ${config.layer2Enabled ? 'bg-indigo-500 shadow-lg shadow-indigo-500/20' : 'bg-slate-200'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-white transition-transform duration-300
              ${config.layer2Enabled ? 'translate-x-7' : 'translate-x-0'}`} />
          </button>
        </div>
        <div className={`p-5 bg-white border border-indigo-50 rounded-[1.5rem] transition-all shadow-sm
          ${!config.layer2Enabled ? 'opacity-40 grayscale pointer-events-none bg-slate-50' : 'hover:border-indigo-100'}`}>
          <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block mb-1">L2 Batch Size</label>
          <input 
            type="number" 
            value={config.layer2BatchSize} 
            onChange={e => setConfig({ ...config, layer2BatchSize: +e.target.value })} 
            disabled={!config.layer2Enabled}
            className="w-full bg-transparent border-none text-xl font-bold outline-none text-indigo-800 p-0"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 mb-5">
        <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center">
          <ShieldCheck size={18} className="text-rose-500" />
        </div>
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest">Security & Resilience</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-12">
        <div className="p-5 bg-white border border-rose-50 rounded-[1.5rem] hover:border-rose-100 transition-all shadow-sm">
          <label className="text-[10px] font-bold text-rose-400 uppercase tracking-widest block mb-1">Malicious Nodes</label>
          <input 
            type="number" 
            value={config.byzantine} 
            onChange={e => setConfig({ ...config, byzantine: +e.target.value })}
            className="w-full bg-transparent border-none text-xl font-bold outline-none text-rose-800 p-0"
          />
        </div>
        <div className="p-5 bg-white border border-rose-50 rounded-[1.5rem] hover:border-rose-100 transition-all shadow-sm">
          <label className="text-[10px] font-bold text-rose-400 uppercase tracking-widest block mb-1">Attack Strategy</label>
          <select 
            value={config.attackType} 
            onChange={e => setConfig({ ...config, attackType: +e.target.value })}
            className="w-full bg-transparent border-none text-sm font-bold outline-none text-rose-800 mt-1 cursor-pointer"
          >
            <option value={0}>None / Honest Only</option>
            <option value={1}>Double Spending Attack</option>
            <option value={2}>Invalid Block Forgery</option>
          </select>
        </div>
      </div>

      <div className="p-6 md:p-8 rounded-[2.5rem] bg-slate-900 text-white flex flex-col md:flex-row items-center justify-between gap-6 shadow-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-3xl rounded-full" />
        <div className="flex items-center gap-5 relative z-10 w-full md:w-auto">
           <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 shrink-0">
              <ChevronRight size={28} />
           </div>
           <div>
              <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Estimated Cloud Cost</p>
              <h3 className="text-3xl font-bold font-mono text-white">
                ${calculateEstimatedCost(selectedCloud, config.fog + config.miners).toFixed(4)}
                <span className="text-xs text-slate-500 ml-2 font-sans font-normal uppercase tracking-tighter">per hour</span>
              </h3>
           </div>
        </div>
        <button
          onClick={onSave}
          className="w-full md:w-auto px-10 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-2xl font-bold hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-cyan-500/25 relative z-10"
        >
          Finalize Specs
        </button>
      </div>
    </>
  );
}
