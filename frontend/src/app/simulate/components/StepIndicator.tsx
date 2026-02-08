import React from "react";

interface StepIndicatorProps {
  currentStep: number;
  steps: string[];
}

export default function StepIndicator({ currentStep, steps }: StepIndicatorProps) {
  return (
    <div style={{ maxWidth: 700, margin: "0 auto 30px", padding: "0 20px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", position: "relative" }}>
        <div style={{ position: "absolute", top: 18, left: 35, right: 35, height: 4, background: "#334155", borderRadius: 2 }} />
        <div style={{
          position: "absolute",
          top: 18,
          left: 35,
          width: `${((currentStep - 1) / (steps.length - 1)) * 90}%`,
          height: 4,
          background: "linear-gradient(90deg, #06b6d4, #8b5cf6)",
          borderRadius: 2,
          transition: "width 0.3s"
        }} />
        {steps.map((s, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", zIndex: 2, flex: 1 }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
              background: currentStep > i + 1 ? "#10b981" : currentStep === i + 1 ? "linear-gradient(135deg, #06b6d4, #8b5cf6)" : "#1e293b",
              border: currentStep >= i + 1 ? "none" : "3px solid #334155",
              color: "white", fontWeight: 600, fontSize: 15,
              boxShadow: currentStep === i + 1 ? "0 0 20px rgba(6,182,212,0.5)" : "none"
            }}>{currentStep > i + 1 ? "✓" : i + 1}</div>
            <span style={{ fontSize: 10, marginTop: 8, color: currentStep >= i + 1 ? "#e2e8f0" : "#64748b", textAlign: "center", maxWidth: 80 }}>{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
