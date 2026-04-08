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
      <h2 className="text-xl md:text-2xl font-bold text-slate-900 mb-1">Step 1: Select Blockchain Functions</h2>
      <p className="text-slate-500 mb-8 text-sm md:text-base font-medium">Choose blockchain capabilities.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
        {FUNCTIONS.map(f => (
          <div 
            key={f.id} 
            onClick={() => setSelectedFunc(f.id)} 
            className={`
              p-5 md:p-6 rounded-[1.5rem] cursor-pointer flex gap-4 md:gap-5 transition-all duration-200
              ${selectedFunc === f.id 
                ? "border-2 border-cyan-500 bg-gradient-to-br from-cyan-50/50 to-white shadow-lg shadow-cyan-500/10" 
                : "border-2 border-slate-100 bg-white hover:border-slate-300 hover:shadow-md"}
            `}
          >
            <div 
              className="w-14 h-14 rounded-2xl flex-shrink-0 flex items-center justify-center text-white shadow-lg"
              style={{ background: `linear-gradient(135deg, ${f.color}, ${f.color}cc)`, boxShadow: `0 8px 20px ${f.color}40` }}
            >
              <f.Icon />
            </div>
            <div className="flex flex-col">
              <h3 className="text-base md:text-lg font-bold text-slate-900 leading-tight">{f.name}</h3>
              <p className="text-xs md:text-sm text-slate-500 mt-1 mb-3 leading-relaxed">{f.desc}</p>
              <span className={`
                self-start px-4 py-1.5 rounded-lg text-xs font-bold transition-all
                ${selectedFunc === f.id ? "bg-cyan-500 text-white" : "bg-slate-100 text-slate-500"}
              `}>
                {selectedFunc === f.id ? "✓ Selected" : "Select"}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-10 pt-8 border-t border-slate-100">
        <p className="text-xs md:text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Deployment Layer</p>
        <div className="flex flex-col sm:flex-row gap-4">
          {[
            { id: 1, name: "Fog Layer", icon: "☁️", desc: "Edge computing infrastructure" }, 
            { id: 2, name: "End User", icon: "👤", desc: "Client-side execution" }
          ].map(p => (
            <button 
              key={p.id} 
              onClick={() => setPlacement(p.id)} 
              className={`
                flex-1 p-5 rounded-2xl border-2 transition-all duration-200 text-left flex items-center gap-4
                ${placement === p.id 
                  ? "border-cyan-500 bg-cyan-50/30 text-cyan-900 shadow-sm" 
                  : "border-slate-100 bg-white hover:border-slate-200"}
              `}
            >
              <span className="text-3xl md:text-4xl filter drop-shadow-sm">{p.icon}</span>
              <div>
                <p className="font-bold text-slate-900 text-sm md:text-base">{p.name}</p>
                <p className="text-[10px] md:text-xs text-slate-500 font-medium">{p.desc}</p>
              </div>
              {placement === p.id && <div className="ml-auto w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center text-white text-[10px]">✓</div>}
            </button>
          ))}
        </div>
      </div>
    </>
  );
}
