import React from "react";
import { FUNCTIONS } from "../constants";

interface FunctionSelectorProps {
  selectedFunc: number;
  setSelectedFunc: (id: number) => void;
  placement: number;
  setPlacement: (id: number) => void;
}

export default function FunctionSelector({ selectedFunc, setSelectedFunc, placement, setPlacement }: FunctionSelectorProps) {
  return (
    <>
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
          {[{ id: 1, name: "Fog Layer", icon: "☁️" }, { id: 2, name: "End User", icon: "👤" }].map(p => (
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
    </>
  );
}
