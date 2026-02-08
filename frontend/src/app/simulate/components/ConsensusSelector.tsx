import React from "react";
import { CONSENSUS } from "../constants";

interface ConsensusSelectorProps {
  selectedCons: number;
  setSelectedCons: (id: number) => void;
}

export default function ConsensusSelector({ selectedCons, setSelectedCons }: ConsensusSelectorProps) {
  return (
    <>
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
    </>
  );
}
