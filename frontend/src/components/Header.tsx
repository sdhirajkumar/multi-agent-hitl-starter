import React from 'react';
import { Layers, RotateCcw, ShieldCheck, Zap } from 'lucide-react';

interface HeaderProps {
  status: string;
  threadId: string | null;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({ status, threadId, onReset }) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            Running Agents
          </span>
        );
      case 'interrupted':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-bounce">
            <ShieldCheck className="w-3.5 h-3.5" />
            Paused for Human Approval
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            Deliverable Finalized
          </span>
        );
      case 'resuming':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
            Resuming Execution...
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
            Ready
          </span>
        );
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white tracking-tight">Multi-Agent HITL Starter</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                LangGraph v0.2+
              </span>
            </div>
            <p className="text-xs text-slate-400">Cyclic Agent Orchestrator with Human-in-the-Loop Gate</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {getStatusBadge()}

          {threadId && (
            <div className="hidden md:flex items-center gap-1 text-xs text-slate-400 font-mono bg-slate-800/80 px-2.5 py-1 rounded-md border border-slate-700">
              <span className="text-slate-500">thread:</span>
              <span className="text-sky-300">{threadId.slice(0, 8)}...</span>
            </div>
          )}

          {threadId && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition"
              title="Reset current run"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
