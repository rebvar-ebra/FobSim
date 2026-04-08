import React from "react";
import { Play, Square, rotateCcw as RotateCcw, Trash2 } from "lucide-react";

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
  const getColorClass = (line: string) => {
    if (line.includes("hash:") || line.match(/^[0-9a-f]{64}$/i)) return "text-cyan-400";
    if (line.includes("Error") || line.includes("❌")) return "text-rose-400";
    if (line.includes("⏹️")) return "text-rose-500 font-bold";
    if (line.includes("🖥️ SERVER")) return "text-violet-400 font-bold bg-violet-400/10 px-1 rounded";
    if (line.includes("📊 MONITOR")) return "text-emerald-400 text-[11px] border-l-2 border-emerald-500 pl-2";
    if (line.includes("✅") || line.includes("completed")) return "text-emerald-400 font-bold";
    if (line.includes("✓") || line.includes("Genesis")) return "text-emerald-500";
    if (line.includes("Miner_")) return "text-indigo-400";
    if (line.includes("block") || line.includes("Block")) return "text-amber-400";
    if (line.includes("***")) return "text-slate-500";
    return "text-slate-300";
  };

  return (
    <>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-900 m-0">Step 4: Run Simulation</h2>
          <p className="text-slate-500 text-sm mt-1">Monitor blockchain activity in real-time.</p>
        </div>
        {(running || output.length > 0) && (
          <div className="flex items-center gap-4 bg-slate-100 px-4 py-2 rounded-2xl w-full sm:w-auto justify-center">
            <div className="text-center">
              <div className="text-xl font-bold text-slate-900 font-mono tracking-tighter">{formatTime(elapsed)}</div>
              <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Elapsed</div>
            </div>
          </div>
        )}
      </div>

      {/* Live Stats */}
      {(running || output.length > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mb-6">
          <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-3xl p-6 text-white shadow-lg shadow-cyan-500/20 transition-transform hover:scale-[1.02]">
            <div className="text-4xl font-bold tracking-tighter mb-1">{stats.blocks}</div>
            <div className="text-xs font-bold uppercase tracking-widest opacity-80">Blocks Mined</div>
          </div>
          <div className="bg-gradient-to-br from-violet-500 to-violet-600 rounded-3xl p-6 text-white shadow-lg shadow-violet-500/20 transition-transform hover:scale-[1.02]">
            <div className="text-4xl font-bold tracking-tighter mb-1">{stats.miners}</div>
            <div className="text-xs font-bold uppercase tracking-widest opacity-80">Active Miners</div>
          </div>
          <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-3xl p-6 text-white shadow-lg shadow-emerald-500/20 transition-transform hover:scale-[1.02]">
            <div className="text-4xl font-bold tracking-tighter mb-1">{output.length}</div>
            <div className="text-xs font-bold uppercase tracking-widest opacity-80">Log Lines</div>
          </div>
        </div>
      )}

      {!running && output.length === 0 && (
        <div className="text-center py-20 bg-slate-50/50 rounded-[3rem] border-2 border-dashed border-slate-200">
          <button 
            onClick={onRun} 
            className="group px-10 py-5 bg-gradient-to-r from-cyan-500 to-violet-600 text-white rounded-[2rem] font-bold text-lg hover:brightness-110 active:scale-95 transition-all shadow-2xl shadow-cyan-500/20 flex items-center justify-center gap-3 mx-auto"
          >
            <Play className="fill-white" />
            Start Simulation
          </button>
          <p className="mt-6 text-slate-400 text-sm font-medium">Click to deploy nodes and begin consensus</p>
        </div>
      )}

      {(running || output.length > 0) && (
        <div 
          ref={consoleRef} 
          className="bg-slate-900 rounded-[2rem] p-6 h-[400px] overflow-y-auto font-mono text-[11px] md:text-xs shadow-2xl border border-slate-800 relative group"
        >
          {output.map((l, i) => (
            <div key={i} className={`flex gap-4 py-1 border-b border-slate-800/30 ${getColorClass(l)}`}>
              <span className="text-slate-600 w-8 shrink-0 select-none text-right font-bold">{String(i + 1).padStart(3, "0")}</span>
              <span className="break-all">{l}</span>
            </div>
          ))}
          {running && (
            <div className="flex items-center gap-2 text-cyan-400 mt-2 font-bold animate-pulse">
              <span className="w-2 h-4 bg-cyan-500" />
              Processing consensus...
            </div>
          )}
          {!running && output.length > 0 && (
            <div className="mt-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 font-bold flex items-center justify-center gap-2">
              ✓ Simulation completed in {formatTime(elapsed)}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {(running || output.length > 0) && (
        <div className="flex flex-wrap gap-4 mt-8">
          {running && (
            <button 
              onClick={onStop} 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-4 bg-white border-2 border-rose-100 rounded-2xl text-rose-500 font-bold hover:bg-rose-50 transition-all active:scale-95"
            >
              <Square size={20} className="fill-rose-500" />
              Stop
            </button>
          )}
          {!running && (
            <button 
              onClick={onClear} 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-4 bg-white border-2 border-slate-200 rounded-2xl text-slate-500 font-bold hover:bg-slate-50 transition-all active:scale-95"
            >
              <Trash2 size={20} />
              Clear Console
            </button>
          )}
          {!running && (
            <button 
              onClick={onRun} 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-2xl font-bold shadow-lg shadow-cyan-500/20 hover:brightness-110 transition-all active:scale-95"
            >
              <Play size={20} className="fill-white" />
              Run Again
            </button>
          )}
        </div>
      )}
    </>
  );
}
