import React from "react";

interface SimulationRunnerProps {
  running: boolean;
  output: string[];
  elapsed: number;
  stats: { blocks: number; miners: number; transactions: number };
  onRun: () => void;
  onStop: () => void;
  onClear: () => void;
  consoleRef: React.RefObject<HTMLDivElement | null>;
  formatTime: (s: number) => string;
}

export default function SimulationRunner({ running, output, elapsed, stats, onRun, onStop, onClear, consoleRef, formatTime }: SimulationRunnerProps) {
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

  return (
    <>
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
          <button onClick={onRun} style={{
            padding: "16px 40px", borderRadius: 14, border: "none", cursor: "pointer", fontSize: 17, fontWeight: 600, color: "white",
            background: "linear-gradient(135deg, #06b6d4, #8b5cf6)", boxShadow: "0 10px 40px rgba(6,182,212,0.4)"
          }}>▶ Start Simulation</button>
        </div>
      )}

      {(running || output.length > 0) && (
        <div ref={consoleRef} style={{ background: "#0f172a", borderRadius: 12, padding: 16, height: 280, overflowY: "auto", fontFamily: "'SF Mono', 'Monaco', monospace", fontSize: 12 }}>
          {output.map((l, i) => (
            <div key={i} style={{ ...colorize(l), padding: "2px 0" }}>
              <span style={{ color: "#475569", marginRight: 10, userSelect: "none" }}>{String(i + 1).padStart(3, "0")}</span>{l}
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
            <button onClick={onStop} style={{ padding: "10px 20px", borderRadius: 10, border: "2px solid #ef4444", background: "transparent", color: "#ef4444", fontWeight: 500, cursor: "pointer" }}>
              ⏹ Stop
            </button>
          )}
          {!running && (
            <button onClick={onClear} style={{ padding: "10px 20px", borderRadius: 10, border: "2px solid #64748b", background: "transparent", color: "#64748b", fontWeight: 500, cursor: "pointer" }}>
              🗑 Clear
            </button>
          )}
          {!running && (
            <button onClick={onRun} style={{ padding: "10px 20px", borderRadius: 10, border: "none", background: "linear-gradient(135deg, #06b6d4, #8b5cf6)", color: "white", fontWeight: 500, cursor: "pointer" }}>
              ▶ Run Again
            </button>
          )}
        </div>
      )}
    </>
  );
}
