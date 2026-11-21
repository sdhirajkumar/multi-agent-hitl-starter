import React from 'react';
import { 
  Bot, 
  Search, 
  PenTool, 
  CheckCircle2, 
  ShieldAlert, 
  Send, 
  ArrowRight,
  Clock,
  Sparkles,
  Check
} from 'lucide-react';
import { AgentNodeName, WorkflowState } from '../types';

interface AgentTimelineProps {
  state: WorkflowState;
}

interface StepConfig {
  id: AgentNodeName;
  name: string;
  role: string;
  icon: React.ReactNode;
  description: string;
}

const STEPS: StepConfig[] = [
  {
    id: 'supervisor',
    name: 'Supervisor',
    role: 'Orchestrator',
    icon: <Bot className="w-4 h-4" />,
    description: 'Plans tasks & routes to specialists',
  },
  {
    id: 'researcher',
    name: 'Researcher',
    role: 'Context Gatherer',
    icon: <Search className="w-4 h-4" />,
    description: 'Collects facts & technical constraints',
  },
  {
    id: 'writer',
    name: 'Writer',
    role: 'Synthesizer',
    icon: <PenTool className="w-4 h-4" />,
    description: 'Drafts deliverable in markdown',
  },
  {
    id: 'reviewer',
    name: 'Reviewer',
    role: 'Critic',
    icon: <CheckCircle2 className="w-4 h-4" />,
    description: 'Audits quality & prompts revision',
  },
  {
    id: 'human_review',
    name: 'Human Gate',
    role: 'HITL Reviewer',
    icon: <ShieldAlert className="w-4 h-4" />,
    description: 'Dynamic pause for human approval/edit/critique',
  },
  {
    id: 'publisher',
    name: 'Publisher',
    role: 'Finalizer',
    icon: <Send className="w-4 h-4" />,
    description: 'Publishes verified deliverable',
  },
];

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ state }) => {
  const { currentNode, isInterrupted, status, revisionCount, plan, researchData } = state;

  // Determine which step is currently active or completed
  const getNodeStatus = (stepId: AgentNodeName, idx: number) => {
    if (status === 'idle') return 'pending';
    if (status === 'completed') return 'completed';

    if (stepId === currentNode) {
      return isInterrupted ? 'interrupted' : 'active';
    }

    const nodeOrder: AgentNodeName[] = ['supervisor', 'researcher', 'writer', 'reviewer', 'human_review', 'publisher'];
    const currentIdx = currentNode ? nodeOrder.indexOf(currentNode) : -1;

    if (currentIdx > idx) return 'completed';
    return 'pending';
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-sky-400" />
          <h2 className="text-sm font-bold text-white tracking-tight">Agent Execution Pipeline</h2>
        </div>
        {revisionCount > 0 && (
          <span className="text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2.5 py-0.5 rounded-full font-medium">
            Revision Loop #{revisionCount}
          </span>
        )}
      </div>

      {/* Stepper Grid */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {STEPS.map((step, idx) => {
          const stepStatus = getNodeStatus(step.id, idx);
          const isActive = stepStatus === 'active';
          const isCompleted = stepStatus === 'completed';
          const isInterruptedStep = stepStatus === 'interrupted';

          return (
            <div
              key={step.id}
              className={`relative rounded-xl p-3 border transition-all duration-300 flex flex-col justify-between ${
                isInterruptedStep
                  ? 'bg-rose-950/30 border-rose-500/60 shadow-lg shadow-rose-500/10 ring-1 ring-rose-500'
                  : isActive
                  ? 'bg-sky-950/40 border-sky-500 shadow-lg shadow-sky-500/10 ring-1 ring-sky-500'
                  : isCompleted
                  ? 'bg-slate-800/60 border-emerald-500/40 text-slate-300'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-500 opacity-60'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isInterruptedStep
                        ? 'bg-rose-500 text-white animate-bounce'
                        : isActive
                        ? 'bg-sky-500 text-white animate-pulse'
                        : isCompleted
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : step.icon}
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">0{idx + 1}</span>
                </div>

                <div className="text-xs font-semibold text-slate-100 flex items-center gap-1">
                  {step.name}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">{step.role}</div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60">
                <span
                  className={`inline-block text-[10px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded ${
                    isInterruptedStep
                      ? 'bg-rose-500/20 text-rose-300'
                      : isActive
                      ? 'bg-sky-500/20 text-sky-300'
                      : isCompleted
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-slate-800/60 text-slate-500'
                  }`}
                >
                  {isInterruptedStep ? 'Action Req' : isActive ? 'Working' : isCompleted ? 'Finished' : 'Waiting'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic State Info Box: Plan & Research items */}
      {(plan.length > 0 || researchData.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
          {plan.length > 0 && (
            <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3">
              <span className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider block mb-1">
                Active Execution Plan (Supervisor)
              </span>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {plan.map((item, i) => (
                  <li key={i} className="line-clamp-1">{item}</li>
                ))}
              </ul>
            </div>
          )}

          {researchData.length > 0 && (
            <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3">
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                Gathered Research Findings ({researchData.length} items)
              </span>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {researchData.slice(0, 3).map((item, i) => (
                  <li key={i} className="line-clamp-1">{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
