"use client";

import { useState, useEffect, useRef } from "react";
import { API_URL } from "../api";
import { CLOUD_PROVIDERS } from "../utils/cloud_pricing";
import { STEPS, FUNCTIONS, CONSENSUS, BlockchainCubeIcon } from "./constants";

// Components
import StepIndicator from "./components/StepIndicator";
import FunctionSelector from "./components/FunctionSelector";
import ConsensusSelector from "./components/ConsensusSelector";
import ParameterConfig from "./components/ParameterConfig";
import SimulationRunner from "./components/SimulationRunner";

export default function Dashboard() {
  const [step, setStep] = useState(1);
  const [selectedFunc, setSelectedFunc] = useState(0);
  const [selectedCons, setSelectedCons] = useState(0);
  const [placement, setPlacement] = useState(1);
  const [config, setConfig] = useState({ fog: 5, miners: 4, tx: 5, diff: 2 });
  const [selectedCloud, setSelectedCloud] = useState(CLOUD_PROVIDERS[0].id);
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [stats, setStats] = useState({ blocks: 0, miners: 0, transactions: 0 });
  const consoleRef = useRef<HTMLDivElement | null>(null);
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
    setStats({ blocks: Math.floor(blocks / 2), miners: Math.min(miners, config.miners), transactions: txs });
  }, [output, config.miners]);

  useEffect(() => {
    if (running) {
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [running]);

  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${((s % 60)).toString().padStart(2, '0')}`;

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

  const handleSaveSettings = async () => {
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
  };

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

      <StepIndicator currentStep={step} steps={STEPS} />

      {/* Main Card */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 20px 40px" }}>
        <div style={{ background: "white", borderRadius: 20, padding: 32, boxShadow: "0 25px 60px rgba(0,0,0,0.3)" }}>

          {step === 1 && (
            <FunctionSelector
              selectedFunc={selectedFunc}
              setSelectedFunc={setSelectedFunc}
              placement={placement}
              setPlacement={setPlacement}
            />
          )}

          {step === 2 && (
            <ConsensusSelector
              selectedCons={selectedCons}
              setSelectedCons={setSelectedCons}
            />
          )}

          {step === 3 && (
            <ParameterConfig
              config={config}
              setConfig={setConfig}
              selectedCloud={selectedCloud}
              setSelectedCloud={setSelectedCloud}
              configError={configError}
              onSave={handleSaveSettings}
            />
          )}

          {step === 4 && (
            <SimulationRunner
              running={running}
              output={output}
              elapsed={elapsed}
              stats={stats}
              onRun={runSim}
              onStop={stopSim}
              onClear={() => { setOutput([]); setElapsed(0); }}
              consoleRef={consoleRef}
              formatTime={formatTime}
            />
          )}

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
