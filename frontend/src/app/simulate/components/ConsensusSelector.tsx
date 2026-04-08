import React from "react";
import { CONSENSUS } from "../constants";

interface ConsensusSelectorProps {
  selectedCons: number;
  setSelectedCons: (id: number) => void;
}

export default function ConsensusSelector({ selectedCons, setSelectedCons }: ConsensusSelectorProps) {
  return (
    <>
      <h2 className="text-xl md:text-2xl font-bold text-slate-900 mb-1">Step 2: Choose Consensus</h2>
      <p className="text-slate-500 mb-8 text-sm md:text-base font-medium">Select network agreement protocol.</p>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
        {CONSENSUS.map(c => (
          <div 
            key={c.id} 
            onClick={() => setSelectedCons(c.id)} 
            className={`
              p-4 md:p-5 rounded-2xl cursor-pointer flex items-center gap-4 transition-all duration-200
              ${selectedCons === c.id 
                ? "border-2 border-cyan-500 bg-cyan-50/30 shadow-sm" 
                : "border-2 border-slate-100 bg-white hover:border-slate-200 hover:bg-slate-50/50"}
            `}
          >
            <div 
              className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-[10px] md:text-xs shrink-0 shadow-md"
              style={{ background: c.color }}
            >
              {c.short}
            </div>
            <span className={`flex-1 text-sm md:text-base font-bold ${selectedCons === c.id ? "text-slate-900" : "text-slate-700"}`}>
              {c.name}
            </span>
            {selectedCons === c.id && (
              <div className="w-6 h-6 rounded-full bg-cyan-500 flex items-center justify-center text-white text-xs">
                ✓
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
