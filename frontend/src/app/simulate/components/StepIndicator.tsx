import React from "react";

interface StepIndicatorProps {
  currentStep: number;
  steps: string[];
}

export default function StepIndicator({ currentStep, steps }: StepIndicatorProps) {
  const progressWidth = `${((currentStep - 1) / (steps.length - 1)) * 100}%`;

  return (
    <div className="max-w-2xl mx-auto mb-10 px-5">
      <div className="flex items-start justify-between relative">
        {/* Background Line */}
        <div className="absolute top-[18px] left-[20px] right-[20px] h-1 bg-slate-700 rounded-full" />
        
        {/* Progress Line */}
        <div 
          className="absolute top-[18px] left-[20px] h-1 bg-gradient-to-r from-cyan-500 to-violet-600 rounded-full transition-all duration-500"
          style={{ width: `calc(${progressWidth} - 40px)` }}
        />

        {steps.map((s, i) => (
          <div key={i} className="flex flex-col items-center z-10 flex-1">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300
              ${currentStep > i + 1 
                ? "bg-emerald-500 text-white" 
                : currentStep === i + 1 
                  ? "bg-gradient-to-br from-cyan-500 to-violet-600 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)] scale-110" 
                  : "bg-slate-800 text-slate-500 border-2 border-slate-700"}
            `}>
              {currentStep > i + 1 ? "✓" : i + 1}
            </div>
            <span className={`
              text-[10px] md:text-xs mt-3 text-center max-w-[80px] font-medium transition-colors
              ${currentStep >= i + 1 ? "text-slate-200" : "text-slate-500"}
            `}>
              {s}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
