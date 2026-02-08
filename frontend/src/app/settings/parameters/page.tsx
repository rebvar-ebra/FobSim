"use client";

import React, { useState, useEffect } from "react";
import { API_URL } from "../../api";
import { Save, RefreshCw, AlertCircle, CheckCircle2, ChevronLeft, Network, Shield, Zap, Info, ToggleLeft, ToggleRight, Lock } from "lucide-react";
import Link from "next/link";

export default function AdvancedSettings() {
  const [params, setParams] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);

  useEffect(() => {
    fetchParams();
  }, []);

  const fetchParams = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/config`);
      const data = await res.json();
      setParams(data);
    } catch (err) {
      setStatus({ type: 'error', msg: 'Failed to load parameters.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setStatus(null);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API_URL}/api/config`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(params)
      });
      if (res.ok) {
        setStatus({ type: 'success', msg: 'Parameters updated!' });
      } else {
        throw new Error();
      }
    } catch (err) {
      setStatus({ type: 'error', msg: 'Failed to save changes.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
    </div>
  );

  // Categorization Logic
  const categories = [
    {
      id: "network",
      name: "Network Topology",
      icon: <Network className="text-blue-400" size={18} />,
      keys: [
        "NumOfFogNodes",
        "num_of_users_per_fog_node",
        "NumOfMiners",
        "number_of_each_miner_neighbours",
        "delay_between_fog_nodes",
        "delay_between_end_users"
      ]
    },
    {
      id: "consensus",
      name: "Consensus & Engine",
      icon: <Shield className="text-violet-400" size={18} />,
      keys: [
        "puzzle_difficulty",
        "poet_block_time",
        "numOfTXperBlock",
        "mining_award",
        "Num_of_DPoS_delegates",
        "Automatic_PoA_miners_authorization?",
        "Parallel_PoW_mining?"
      ]
    },
    {
      id: "security",
      name: "Transaction & Security",
      icon: <Lock className="text-emerald-400" size={18} />,
      keys: [
        "NumOfTaskPerUser",
        "Max_enduser_payment",
        "miners_initial_wallet_value",
        "Asymmetric_key_length",
        "Gossip_Activated",
        "STOR_PLC(0=in the Fog,1=in the BC)"
      ]
    }
  ];

  const renderField = (key: string) => {
    const value = params[key];
    if (value === undefined) return null;

    const isBoolean = typeof value === 'boolean';
    const isSelect = key.includes("STOR_PLC");

    return (
      <div key={key} className="flex items-center justify-between py-3 border-b border-slate-800/50 last:border-0 group">
        <div className="flex items-center gap-2 max-w-[60%]">
          <label className="text-sm font-medium text-slate-300 capitalize">
            {key.replace(/_/g, ' ').replace(/\?/g, '').replace(/\(.*\)/, '')}
          </label>
          <Info size={12} className="text-slate-600 opacity-0 group-hover:opacity-100 transition cursor-help shrink-0" />
        </div>

        <div className="flex items-center gap-3">
          {isBoolean ? (
            <button
              onClick={() => setParams({ ...params, [key]: !value })}
              className={`flex items-center transition-colors ${value ? 'text-cyan-400' : 'text-slate-600'}`}
            >
              {value ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
            </button>
          ) : isSelect ? (
            <select
              value={value}
              onChange={(e) => setParams({ ...params, [key]: +e.target.value })}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-cyan-400 outline-none focus:border-cyan-500 transition font-mono"
            >
              <option value={0}>Fog Storage (0)</option>
              <option value={1}>BC Storage (1)</option>
            </select>
          ) : (
            <input
              type={typeof value === 'number' ? 'number' : 'text'}
              step={key.includes("delay") ? "0.1" : "1"}
              value={value}
              onChange={(e) => setParams({ ...params, [key]: typeof value === 'number' ? +e.target.value : e.target.value })}
              className="w-24 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-cyan-400 outline-none focus:border-cyan-500 transition font-mono text-right"
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/settings" className="p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition">
            <ChevronLeft size={20} />
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white uppercase tracking-tight">Advanced Parameters</h1>
            <p className="text-slate-400 text-sm mt-1">Direct control hub for <code className="text-cyan-500">Sim_parameters.json</code> schema.</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {status && (
            <span className={`text-sm font-medium ${status.type === 'success' ? 'text-emerald-400' : 'text-rose-400'} animate-in fade-in slide-in-from-right-2`}>
              {status.msg}
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition ${
              saving ? 'bg-slate-700 cursor-not-allowed text-slate-500' : 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:brightness-110 shadow-lg shadow-cyan-500/20'
            }`}
          >
            {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
            {saving ? 'Syncing...' : 'Deploy Changes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {categories.map((cat) => (
          <div key={cat.id} className="flex flex-col h-full bg-slate-900/50 border border-slate-800 rounded-[2rem] p-6 hover:bg-slate-900/80 transition duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shadow-inner">
                {cat.icon}
              </div>
              <h3 className="font-bold text-white tracking-wide">{cat.name}</h3>
            </div>
            <div className="flex-1 space-y-1">
              {cat.keys.map(renderField)}
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 rounded-[2rem] bg-amber-500/5 border border-amber-500/10 flex items-start gap-5">
        <AlertCircle className="text-amber-500 shrink-0 mt-1" size={24} />
        <div className="space-y-2">
            <h4 className="text-white font-bold">Research Notice</h4>
            <p className="text-slate-400 text-sm leading-relaxed">
              These parameters represent the raw physical logic of the simulation engine. Changes here will instantly persist to the backend and affect all subsequent experiment runs. Use the <code className="text-cyan-500">Syncing...</code> phase to ensure data integrity across the cluster.
            </p>
        </div>
      </div>
    </div>
  );
}
