import React, { useState } from 'react';
import { Copy, Check, Download, FileCheck, ExternalLink, Sparkles } from 'lucide-react';

interface OutputViewerProps {
  content: string;
  status: string;
  revisionCount: number;
  threadId: string | null;
}

export const OutputViewer: React.FC<OutputViewerProps> = ({
  content,
  status,
  revisionCount,
  threadId,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!content) return;
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `deliverable-${threadId ? threadId.slice(0, 8) : 'draft'}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!content) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center text-slate-500">
        <FileCheck className="w-10 h-10 mx-auto text-slate-700 mb-3" />
        <p className="text-sm font-medium">Deliverable draft will appear here as agents write and finalize.</p>
        <p className="text-xs text-slate-600 mt-1">
          The Writer Agent compiles research, passes through Reviewer audit, and pauses at the Human Gate.
        </p>
      </div>
    );
  }

  const wordCount = content.trim().split(/\s+/).length;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-white tracking-tight">
            {status === 'completed' ? 'Final Verified Deliverable' : 'Current Working Draft'}
          </h2>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
            {wordCount} words
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied!' : 'Copy Markdown'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download .md</span>
          </button>
        </div>
      </div>

      {/* Rendered Markdown or Text Document */}
      <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-5 font-sans text-sm text-slate-200 leading-relaxed max-h-[500px] overflow-y-auto whitespace-pre-wrap select-text">
        {content}
      </div>
    </div>
  );
};
