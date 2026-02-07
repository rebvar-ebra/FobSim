"use client";

import { useState, useEffect, useRef } from "react";

import { API_URL } from "../api";

// SVG Icons
const DatabaseIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);
const ComputeIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>
  </svg>
);
const PaymentIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="4" width="22" height="16" rx="2"/><path d="M1 10h22"/>
  </svg>
);
const FingerprintIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12C2 6.5 6.5 2 12 2a10 10 0 0 1 8 4"/><path d="M5 19.5C5.5 18 6 15 6 12c0-.7.12-1.37.34-2"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/>
  </svg>
);

const BlockchainCubeIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    <path d="M32 8L52 20V44L32 56L12 44V20L32 8Z" stroke="white" strokeWidth="2" fill="none"/>
    <path d="M32 8V32M32 32L52 20M32 32L12 20M32 32V56M32 32L52 44M32 32L12 44" stroke="white" strokeWidth="1.5" opacity="0.6"/>
    <circle cx="32" cy="8" r="3" fill="white"/><circle cx="52" cy="20" r="3" fill="white"/><circle cx="12" cy="20" r="3" fill="white"/>
    <circle cx="52" cy="44" r="3" fill="white"/><circle cx="12" cy="44" r="3" fill="white"/><circle cx="32" cy="56" r="3" fill="white"/><circle cx="32" cy="32" r="4" fill="white"/>
  </svg>
);

const FUNCTIONS = [
  { id: 1, name: "Data Storage", desc: "Secure, decentralized data storage with immutable records.", Icon: DatabaseIcon, color: "#3b82f6" },
  { id: 2, name: "Compute", desc: "Distributed computing for smart contracts.", Icon: ComputeIcon, color: "#8b5cf6" },
  { id: 3, name: "Payment", desc: "Fast digital asset transfers and transactions.", Icon: PaymentIcon, color: "#10b981" },
  { id: 4, name: "Identity", desc: "Decentralized identity and authentication.", Icon: FingerprintIcon, color: "#f59e0b" },
];

const CONSENSUS = [
  { id: 1, name: "Proof of Work", short: "PoW", color: "#f97316" },
  { id: 2, name: "Proof of Stake", short: "PoS", color: "#22c55e" },
  { id: 3, name: "Proof of Authority", short: "PoA", color: "#3b82f6" },
  { id: 4, name: "Proof of Elapsed Time", short: "PoET", color: "#a855f7" },
  { id: 5, name: "Delegated PoS", short: "DPoS", color: "#ec4899" },
  { id: 6, name: "PBFT", short: "PBFT", color: "#ef4444" },
  { id: 8, name: "Proof of Activity", short: "PoA-H", color: "#06b6d4" },
  { id: 9, name: "Proof of Burn", short: "PoB", color: "#eab308" },
];

export default function Dashboard() {
  const [step, setStep] = useState(1);
  const [selectedFunc, setSelectedFunc] = useState(0);
  const [selectedCons, setSelectedCons] = useState(0);
  const [placement, setPlacement] = useState(1);
  const [config, setConfig] = useState({ fog: 5, miners: 4, tx: 5, diff: 2 });
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [stats, setStats] = useState({ blocks: 0, miners: 0, transactions: 0 });
  const consoleRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch current config on mount
    console.log("Fetching config from:", `${API_URL}/api/config`);
    fetch(`${API_URL}/api/config`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log("Received config:", data);
        if (!data || typeof data !== 'object') {
            throw new Error("Invalid config data received");
        }
        setConfig({
          fog: data.NumOfFogNodes || 5,
          miners: data.NumOfMiners || 4,
          tx: data.numOfTXperBlock || 5,
          diff: data.puzzle_difficulty || 2
        });
        setConfigError(null);
      })
      .catch((err) => {
        console.error("Config fetch error:", err);
        setConfigError("Failed to load parameters from server.");
      });
  }, []);

  useEffect(() => {
    if (consoleRef.current) consoleRef.current.scrollTop = consoleRef.current.scrollHeight;

    // Parse stats from output
    let blocks = 0, miners = 0, txs = 0;
    output.forEach(line => {
      if (line.includes("block has been proposed") || line.includes("Block")) blocks++;
      // More robust miner counting
      if (line.includes("Miner_") || line.includes("Miners have been initiated")) {
        if (line.includes("Miner_")) miners++;
        else miners = config.miners; // Assume all are active if initiated
      }
      if (line.includes("transaction") || line.includes("TX")) txs++;
    });
    setStats({ blocks: Math.floor(blocks/2), miners: Math.min(miners, config.miners), transactions: txs });
  }, [output, config.miners]);

  useEffect(() => {
    if (running) {
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [running]);

  const formatTime = (s: number) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`;

  const runSim = async () => {
    setRunning(true);
    setStep(4);
    setOutput(["🚀 Initializing blockchain environment..."]);
    setElapsed(0);
    setStats({ blocks: 0, miners: 0, transactions: 0 });

    const token = localStorage.getItem("token");

    try {
      await fetch(`${API_URL}/api/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          blockchain_function: selectedFunc,
          blockchain_placement: placement,
          consensus_algorithm: selectedCons,
          config: {
            NumOfFogNodes: config.fog,
            NumOfMiners: config.miners,
            numOfTXperBlock: config.tx,
            puzzle_difficulty: config.diff
          }
        }),
      });
      const poll = setInterval(async () => {
        const res = await fetch(`${API_URL}/api/status`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const d = await res.json();
        setOutput(d.output);
        if (!d.running) { setRunning(false); clearInterval(poll); }
      }, 500);
    } catch { setOutput(["❌ Connection error. Is the setup correct?"]); setRunning(false); }
  };

  const stopSim = async () => {
    setRunning(false); // Immediate UI feedback
    try {
      await fetch(`${API_URL}/api/stop`, { method: "POST" });
      setOutput(prev => [...prev, "⏹️ Simulation stopped by user"]);
    } catch {
      setOutput(prev => [...prev, "❌ Error stopping simulation"]);
    }
  };

  // Colorize console output
  const colorize = (line: string) => {
    if (line.includes("hash:") || line.match(/^[0-9a-f]{64}$/i)) return { color: "#06b6d4" };
    if (line.includes("Error") || line.includes("❌")) return { color: "#ef4444" };
    if (line.includes("⏹️")) return { color: "#ef4444", fontWeight: "bold" };
    if (line.includes("🖥️ SERVER")) return { color: "#a855f7", fontWeight: "bold", background: "rgba(168, 85, 247, 0.1)", padding: "2px 4px", borderRadius: "4px" };
    if (line.includes("📊 MONITOR")) return { color: "#10b981", fontSize: "12px", borderLeft: "2px solid #10b981", paddingLeft: "8px" };
    if (line.includes("✅") || line.includes("completed")) return { color: "#10b981", fontWeight: "bold" };
    if (line.includes("✓") || line.includes("Genesis")) return { color: "#10b981" };
    if (line.includes("Miner_")) return { color: "#a78bfa" };
    if (line.includes("block") || line.includes("Block")) return { color: "#fbbf24" };
    if (line.includes("***")) return { color: "#64748b" };
    return { color: "#e2e8f0" };
  };

  const steps = ["Select Functions", "Configure Network", "Simulate Transactions", "Analyze Results"];

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%)" }}>
      {/* Hero */}
      <div style={{ textAlign: "center", paddingTop: 40, paddingBottom: 20 }}>
        <div style={{
          width: 100, height: 100, borderRadius: 20, margin: "0 auto 20px",
          background: "linear-gradient(135deg, #7c3aed, #a855f7)",
          boxShadow: "0 0 60px rgba(167,139,250,0.5)",
          display: "flex", alignItems: "center", justifyContent: "center"
        }}>
          <BlockchainCubeIcon />
        </div>
        <h1 style={{ fontSize: 42, fontWeight: 700, color: "white", margin: 0 }}>FobSim</h1>
        <p style={{ color: "#a5b4fc", fontSize: 15, marginTop: 6 }}>Advanced Blockchain Simulation Platform</p>
      </div>

      {/* Steps */}
      <div style={{ maxWidth: 700, margin: "0 auto 30px", padding: "0 20px" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", position: "relative" }}>
          <div style={{ position: "absolute", top: 18, left: 35, right: 35, height: 4, background: "#334155", borderRadius: 2 }} />
          <div style={{ position: "absolute", top: 18, left: 35, width: `${((step - 1) / 3) * 90}%`, height: 4, background: "linear-gradient(90deg, #06b6d4, #8b5cf6)", borderRadius: 2, transition: "width 0.3s" }} />
          {steps.map((s, i) => (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", zIndex: 2, flex: 1 }}>
              <div style={{
                width: 40, height: 40, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                background: step > i + 1 ? "#10b981" : step === i + 1 ? "linear-gradient(135deg, #06b6d4, #8b5cf6)" : "#1e293b",
                border: step >= i + 1 ? "none" : "3px solid #334155",
                color: "white", fontWeight: 600, fontSize: 15,
                boxShadow: step === i + 1 ? "0 0 20px rgba(6,182,212,0.5)" : "none"
              }}>{step > i + 1 ? "✓" : i + 1}</div>
              <span style={{ fontSize: 10, marginTop: 8, color: step >= i + 1 ? "#e2e8f0" : "#64748b", textAlign: "center", maxWidth: 80 }}>{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Card */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 20px 40px" }}>
        <div style={{ background: "white", borderRadius: 20, padding: 32, boxShadow: "0 25px 60px rgba(0,0,0,0.3)" }}>

          {step === 1 && <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>Step 1: Select Blockchain Functions</h2>
            <p style={{ color: "#64748b", marginBottom: 24, fontSize: 14 }}>Choose blockchain capabilities.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {FUNCTIONS.map(f => (
                <div key={f.id} onClick={() => setSelectedFunc(f.id)} style={{
                  padding: 20, borderRadius: 14, cursor: "pointer", display: "flex", gap: 14,
                  border: selectedFunc === f.id ? "2px solid #06b6d4" : "2px solid #e2e8f0",
                  background: selectedFunc === f.id ? "linear-gradient(135deg, #f0fdfa, #ecfeff)" : "white",
                  transition: "all 0.15s"
                }}>
                  <div style={{ width: 52, height: 52, borderRadius: 12, flexShrink: 0, background: `linear-gradient(135deg, ${f.color}, ${f.color}cc)`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 4px 15px ${f.color}40` }}>
                    <f.Icon />
                  </div>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: "#0f172a", margin: 0 }}>{f.name}</h3>
                    <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0 10px" }}>{f.desc}</p>
                    <span style={{ padding: "5px 12px", borderRadius: 6, fontSize: 12, fontWeight: 500, background: selectedFunc === f.id ? "#06b6d4" : "#f1f5f9", color: selectedFunc === f.id ? "white" : "#64748b" }}>{selectedFunc === f.id ? "✓ Selected" : "Select"}</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid #e2e8f0" }}>
              <p style={{ fontSize: 12, fontWeight: 600, color: "#64748b", marginBottom: 12 }}>Deployment Layer</p>
              <div style={{ display: "flex", gap: 12 }}>
                {[{id:1,name:"Fog Layer",icon:"☁️"},{id:2,name:"End User",icon:"👤"}].map(p => (
                  <button key={p.id} onClick={() => setPlacement(p.id)} style={{
                    flex: 1, padding: 16, borderRadius: 12, border: placement === p.id ? "2px solid #06b6d4" : "2px solid #e2e8f0",
                    background: placement === p.id ? "#f0fdfa" : "white", cursor: "pointer", textAlign: "center"
                  }}>
                    <span style={{ fontSize: 24 }}>{p.icon}</span>
                    <p style={{ fontWeight: 500, color: "#0f172a", margin: "6px 0 0", fontSize: 13 }}>{p.name}</p>
                  </button>
                ))}
              </div>
            </div>
          </>}

          {step === 2 && <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>Step 2: Choose Consensus</h2>
            <p style={{ color: "#64748b", marginBottom: 24, fontSize: 14 }}>Select network agreement protocol.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {CONSENSUS.map(c => (
                <div key={c.id} onClick={() => setSelectedCons(c.id)} style={{
                  padding: 14, borderRadius: 12, cursor: "pointer", display: "flex", alignItems: "center", gap: 12,
                  border: selectedCons === c.id ? "2px solid #06b6d4" : "2px solid #e2e8f0",
                  background: selectedCons === c.id ? "#f0fdfa" : "white"
                }}>
                  <div style={{ width: 42, height: 42, borderRadius: 10, background: c.color, display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontWeight: 700, fontSize: 10 }}>{c.short}</div>
                  <span style={{ flex: 1, fontSize: 14, fontWeight: 500, color: "#0f172a" }}>{c.name}</span>
                  {selectedCons === c.id && <span style={{ color: "#06b6d4", fontSize: 18 }}>✓</span>}
                </div>
              ))}
            </div>
          </>}

          {step === 3 && <>
            {configError && <p style={{ color: "#ef4444", fontSize: 13, marginBottom: 16 }}>⚠️ {configError}</p>}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {[{k:"fog",l:"Fog Nodes",v:config.fog},{k:"miners",l:"Miners",v:config.miners},{k:"tx",l:"TX/Block",v:config.tx},{k:"diff",l:"Difficulty",v:config.diff}].map(f => (
                <div key={f.k}>
                  <label style={{ fontSize: 12, fontWeight: 500, color: "#64748b" }}>{f.l}</label>
                  <input type="number" value={f.v} onChange={e => setConfig({...config, [f.k]: +e.target.value})}
                    style={{ width: "100%", marginTop: 6, padding: 12, borderRadius: 10, border: "2px solid #e2e8f0", fontSize: 15, outline: "none", boxSizing: "border-box", color: "#0f172a" }}/>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 20, padding: 16, background: "#f8fafc", borderRadius: 12, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, fontSize: 13 }}>
              <div><span style={{ color: "#64748b" }}>Function:</span> <strong style={{ color: "#0f172a" }}>{FUNCTIONS.find(f => f.id === selectedFunc)?.name}</strong></div>
              <div><span style={{ color: "#64748b" }}>Consensus:</span> <strong style={{ color: "#0f172a" }}>{CONSENSUS.find(c => c.id === selectedCons)?.short}</strong></div>
              <div><span style={{ color: "#64748b" }}>Layer:</span> <strong style={{ color: "#0f172a" }}>{placement === 1 ? "Fog" : "End User"}</strong></div>
            </div>
            <button
              onClick={async () => {
                const token = localStorage.getItem("token");
                await fetch(`${API_URL}/api/config`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                  },
                  body: JSON.stringify({
                    NumOfFogNodes: config.fog,
                    NumOfMiners: config.miners,
                    numOfTXperBlock: config.tx,
                    puzzle_difficulty: config.diff
                  })
                });
                alert("Settings saved to Sim_parameters.json!");
              }}
              style={{ marginTop: 16, padding: "8px 16px", borderRadius: 8, border: "1px solid #06b6d4", background: "white", color: "#06b6d4", cursor: "pointer", fontSize: 13, fontWeight: 500 }}
            >
              💾 Save Settings Now
            </button>
          </>}

          {step === 4 && <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", margin: 0 }}>Step 4: Run Simulation</h2>
                <p style={{ color: "#64748b", fontSize: 14, margin: "4px 0 0" }}>Monitor blockchain activity in real-time.</p>
              </div>
              {(running || output.length > 0) && (
                <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 24, fontWeight: 700, color: "#0f172a", fontFamily: "monospace" }}>{formatTime(elapsed)}</div>
                    <div style={{ fontSize: 10, color: "#64748b" }}>Elapsed</div>
                  </div>
                </div>
              )}
            </div>

            {/* Live Stats */}
            {(running || output.length > 0) && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 16 }}>
                <div style={{ background: "linear-gradient(135deg, #06b6d4, #0891b2)", borderRadius: 12, padding: 16, color: "white", textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.blocks}</div>
                  <div style={{ fontSize: 11, opacity: 0.9 }}>Blocks Mined</div>
                </div>
                <div style={{ background: "linear-gradient(135deg, #8b5cf6, #7c3aed)", borderRadius: 12, padding: 16, color: "white", textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.miners}</div>
                  <div style={{ fontSize: 11, opacity: 0.9 }}>Active Miners</div>
                </div>
                <div style={{ background: "linear-gradient(135deg, #10b981, #059669)", borderRadius: 12, padding: 16, color: "white", textAlign: "center" }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{output.length}</div>
                  <div style={{ fontSize: 11, opacity: 0.9 }}>Log Lines</div>
                </div>
              </div>
            )}

            {!running && output.length === 0 && (
              <div style={{ textAlign: "center", padding: 40 }}>
                <button onClick={runSim} style={{
                  padding: "16px 40px", borderRadius: 14, border: "none", cursor: "pointer", fontSize: 17, fontWeight: 600, color: "white",
                  background: "linear-gradient(135deg, #06b6d4, #8b5cf6)", boxShadow: "0 10px 40px rgba(6,182,212,0.4)"
                }}>▶ Start Simulation</button>
              </div>
            )}

            {(running || output.length > 0) && (
              <div ref={consoleRef} style={{ background: "#0f172a", borderRadius: 12, padding: 16, height: 280, overflowY: "auto", fontFamily: "'SF Mono', 'Monaco', monospace", fontSize: 12 }}>
                {output.map((l, i) => (
                  <div key={i} style={{ ...colorize(l), padding: "2px 0" }}>
                    <span style={{ color: "#475569", marginRight: 10, userSelect: "none" }}>{String(i+1).padStart(3,"0")}</span>{l}
                  </div>
                ))}
                {running && <div style={{ color: "#06b6d4", marginTop: 4, animation: "pulse 1s infinite" }}>▋</div>}
                {!running && output.length > 0 && (
                  <div style={{ color: "#10b981", marginTop: 8, padding: "8px 12px", background: "rgba(16,185,129,0.1)", borderRadius: 6, display: "inline-block" }}>
                    ✓ Simulation completed in {formatTime(elapsed)}
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            {(running || output.length > 0) && (
              <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
                {running && (
                  <button onClick={stopSim} style={{ padding: "10px 20px", borderRadius: 10, border: "2px solid #ef4444", background: "transparent", color: "#ef4444", fontWeight: 500, cursor: "pointer" }}>
                    ⏹ Stop
                  </button>
                )}
                {!running && (
                  <button onClick={() => { setOutput([]); setElapsed(0); }} style={{ padding: "10px 20px", borderRadius: 10, border: "2px solid #64748b", background: "transparent", color: "#64748b", fontWeight: 500, cursor: "pointer" }}>
                    🗑 Clear
                  </button>
                )}
                {!running && (
                  <button onClick={runSim} style={{ padding: "10px 20px", borderRadius: 10, border: "none", background: "linear-gradient(135deg, #06b6d4, #8b5cf6)", color: "white", fontWeight: 500, cursor: "pointer" }}>
                    ▶ Run Again
                  </button>
                )}
              </div>
            )}
          </>}

          {/* Navigation */}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 28, paddingTop: 20, borderTop: "1px solid #e2e8f0" }}>
            <button onClick={() => setStep(Math.max(1, step - 1))} disabled={step === 1} style={{
              padding: "10px 20px", borderRadius: 10, border: "none", cursor: step === 1 ? "not-allowed" : "pointer",
              background: "transparent", color: step === 1 ? "#cbd5e1" : "#64748b", fontWeight: 500, fontSize: 14
            }}>← Back</button>
            {step < 4 ? (
              <button onClick={() => setStep(step + 1)} disabled={(step === 1 && !selectedFunc) || (step === 2 && !selectedCons)} style={{
                padding: "10px 28px", borderRadius: 10, border: "none", cursor: "pointer", fontWeight: 600, fontSize: 14, color: "white",
                background: (step === 1 && !selectedFunc) || (step === 2 && !selectedCons) ? "#cbd5e1" : "linear-gradient(135deg, #06b6d4, #8b5cf6)"
              }}>Next →</button>
            ) : null}
          </div>
        </div>
      </div>

      <style>{`@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }`}</style>
    </div>
  );
}
