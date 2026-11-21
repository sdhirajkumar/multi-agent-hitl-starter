import React from 'react';
import { useAgentStream } from './hooks/useAgentStream';
import { Header } from './components/Header';
import { ConfigurationBar } from './components/ConfigurationBar';
import { AgentTimeline } from './components/AgentTimeline';
import { HumanApprovalPanel } from './components/HumanApprovalPanel';
import { OutputViewer } from './components/OutputViewer';
import { LiveLog } from './components/LiveLog';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const { state, startRun, resumeRun, resetRun } = useAgentStream();

  const isWorkflowActive = state.status === 'running' || state.status === 'resuming';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      <Header
        status={state.status}
        threadId={state.thread_id}
        onReset={resetRun}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        {/* Error notification banner */}
        {state.error && (
          <div className="bg-rose-950/40 border border-rose-500/40 rounded-xl p-4 flex items-start gap-3 text-rose-200">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-300">Execution Error</h4>
              <p className="text-xs text-rose-200 mt-0.5">{state.error}</p>
            </div>
          </div>
        )}

        {/* Configuration Bar */}
        <ConfigurationBar
          onStart={startRun}
          isLoading={isWorkflowActive}
        />

        {/* Dynamic Execution Pipeline Stepper */}
        <AgentTimeline state={state} />

        {/* Output & Deliverable Viewer */}
        <OutputViewer
          content={state.finalOutput || state.draft}
          status={state.status}
          revisionCount={state.revisionCount}
          threadId={state.thread_id}
        />

        {/* Live Event Log */}
        <LiveLog events={state.events} />
      </main>

      {/* HITL Review Modal (Surfaces automatically upon interrupt event) */}
      {state.isInterrupted && (
        <HumanApprovalPanel
          interruptData={state.interruptData}
          currentDraft={state.draft}
          revisionCount={state.revisionCount}
          onResume={resumeRun}
          isLoading={state.status === 'resuming'}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <p>
          Multi-Agent HITL Starter &bull; Stateful Cyclic Orchestration with LangGraph v0.2+ &bull; FastAPI & React
        </p>
      </footer>
    </div>
  );
};

export default App;
