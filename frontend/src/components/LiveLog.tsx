import React, { useState, useRef, useEffect } from 'react';
import { Terminal, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { WorkflowEvent } from '../types';

interface LiveLogProps {
  events: WorkflowEvent[];
}

export const LiveLog: React.FC<LiveLogProps> = ({ events }) => {
  const [isOpen, setIsOpen] = useState(true);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, isOpen]);

  const getNodeColor = (node?: string) => {
    switch (node) {
      case 'supervisor':
        return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
      case 'researcher':
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'writer':
        return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
      case 'reviewer':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'human_review':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'publisher':
        return 'text-teal-400 bg-teal-500/10 border-teal-500/20';
      default:
        return 'text-slate-400 bg-slate-800 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/40 transition"
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-white tracking-tight">Live Transition Log</h3>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
            {events.length} events
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>

      {isOpen && (
        <div className="p-4 pt-0">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-xs max-h-56 overflow-y-auto space-y-2">
            {events.length === 0 ? (
              <div className="text-slate-500 italic py-2 text-center">Waiting for agent events...</div>
            ) : (
              events.map((ev, i) => (
                <div key={i} className="flex items-start gap-2.5 text-slate-300">
                  <span className="text-[10px] text-slate-600 select-none flex-shrink-0 mt-0.5">
                    {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '--:--:--'}
                  </span>
                  {ev.node && (
                    <span
                      className={`text-[10px] uppercase font-semibold px-1.5 py-0.2 rounded border flex-shrink-0 ${getNodeColor(
                        ev.node
                      )}`}
                    >
                      {ev.node}
                    </span>
                  )}
                  <span className="text-slate-200 break-words flex-1">
                    {ev.detail || ev.action || JSON.stringify(ev)}
                  </span>
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        </div>
      )}
    </div>
  );
};
