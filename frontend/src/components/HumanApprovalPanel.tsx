import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Check, 
  Edit3, 
  RotateCcw, 
  AlertTriangle, 
  FileText,
  MessageSquare,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { InterruptData } from '../types';
import { ResumeParams } from '../services/api';

interface HumanApprovalPanelProps {
  interruptData: InterruptData | null;
  currentDraft: string;
  revisionCount: number;
  onResume: (params: ResumeParams) => void;
  isLoading: boolean;
}

type TabMode = 'approve' | 'edit' | 'reject';

export const HumanApprovalPanel: React.FC<HumanApprovalPanelProps> = ({
  interruptData,
  currentDraft,
  revisionCount,
  onResume,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<TabMode>('approve');
  const [editedDraft, setEditedDraft] = useState<string>(currentDraft || interruptData?.draft || '');
  const [feedback, setFeedback] = useState<string>('');

  // Keep editedDraft in sync if draft changes
  React.useEffect(() => {
    if (currentDraft) setEditedDraft(currentDraft);
    else if (interruptData?.draft) setEditedDraft(interruptData.draft);
  }, [currentDraft, interruptData]);

  const handleApprove = () => {
    onResume({ action: 'approve' });
  };

  const handleEditAndApprove = () => {
    if (!editedDraft.trim()) return;
    onResume({ action: 'edit', edited_draft: editedDraft.trim() });
  };

  const handleRejectWithFeedback = () => {
    onResume({
      action: 'reject',
      feedback: feedback.trim() || 'Please revise and improve clarity, technical depth, and actionable steps.',
    });
  };

  const taskTitle = interruptData?.task || 'Deliverable Draft';
  const critique = interruptData?.critique || '';

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-900/90 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight">Human-in-the-Loop Review Gate</h3>
                <span className="text-[10px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Paused at interrupt()
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Target: <span className="text-slate-200 font-medium">{taskTitle}</span> (Revision #{revisionCount})
              </p>
            </div>
          </div>
        </div>

        {/* Reviewer Critique Banner (if present) */}
        {critique && (
          <div className="bg-indigo-950/40 border-b border-indigo-900/40 p-3.5 px-5 flex items-start gap-2.5 text-xs text-indigo-200">
            <MessageSquare className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold text-indigo-300">Auditor Critique from Reviewer Agent:</span>
              <p className="text-slate-300 line-clamp-2">{critique}</p>
            </div>
          </div>
        )}

        {/* Tab Controls: Approve vs Edit vs Reject */}
        <div className="flex border-b border-slate-800 bg-slate-950/50 px-5 pt-3 gap-2">
          <button
            onClick={() => setActiveTab('approve')}
            className={`flex items-center gap-2 pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
              activeTab === 'approve'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Check className="w-3.5 h-3.5" />
            <span>1. Approve As-Is</span>
          </button>

          <button
            onClick={() => setActiveTab('edit')}
            className={`flex items-center gap-2 pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
              activeTab === 'edit'
                ? 'border-sky-500 text-sky-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>2. Directly Edit Text</span>
          </button>

          <button
            onClick={() => setActiveTab('reject')}
            className={`flex items-center gap-2 pb-2.5 px-3 text-xs font-semibold border-b-2 transition ${
              activeTab === 'reject'
                ? 'border-amber-500 text-amber-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>3. Request Revision with Critique</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {activeTab === 'approve' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Inspect the draft compiled by the Writer agent:</span>
                <span className="font-mono">{editedDraft.length} characters</span>
              </div>
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 max-h-[380px] overflow-y-auto font-mono text-xs text-slate-200 leading-relaxed whitespace-pre-wrap select-text">
                {editedDraft || 'No draft content available.'}
              </div>
            </div>
          )}

          {activeTab === 'edit' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Modify the draft directly in the editor below before publication:</span>
                <span className="font-mono text-sky-400">{editedDraft.length} chars</span>
              </div>
              <textarea
                rows={14}
                value={editedDraft}
                onChange={e => setEditedDraft(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 font-mono text-xs text-slate-100 leading-relaxed focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              />
            </div>
          )}

          {activeTab === 'reject' && (
            <div className="space-y-4">
              <div className="bg-amber-950/20 border border-amber-500/20 rounded-xl p-3.5 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-200">
                  Rejecting will loop execution back to the <strong>Writer Agent</strong> via the Supervisor. 
                  Provide constructive critique to guide the revision cycle.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Human Critique & Required Modifications
                </label>
                <textarea
                  rows={6}
                  value={feedback}
                  onChange={e => setFeedback(e.target.value)}
                  placeholder="e.g. Include SLA breakdown for primary failover, specify on-call escalation phones, and ground MTTR targets under 10 minutes..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                />
              </div>

              {/* Quick feedback suggestions */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] text-slate-400">Quick Prompts:</span>
                {[
                  'Add detailed architectural diagram description',
                  'Include concrete P99 latency SLA metrics',
                  'Flesh out step-by-step incident runbook table',
                ].map((sugg, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setFeedback(prev => prev ? `${prev}\n- ${sugg}` : `- ${sugg}`)}
                    className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700 transition"
                  >
                    + {sugg}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className="p-4 px-5 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            Resumes LangGraph via <code className="text-sky-300 font-mono">Command(resume=...)</code>
          </span>

          <div className="flex items-center gap-3">
            {activeTab === 'approve' && (
              <button
                onClick={handleApprove}
                disabled={isLoading}
                className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-emerald-600/20 transition cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>Approve & Finalize Deliverable</span>
              </button>
            )}

            {activeTab === 'edit' && (
              <button
                onClick={handleEditAndApprove}
                disabled={isLoading || !editedDraft.trim()}
                className="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-sky-600/20 transition cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>Save Edits & Publish</span>
              </button>
            )}

            {activeTab === 'reject' && (
              <button
                onClick={handleRejectWithFeedback}
                disabled={isLoading}
                className="inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-amber-600/20 transition cursor-pointer"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Send Revision Back to Writer</span>
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
