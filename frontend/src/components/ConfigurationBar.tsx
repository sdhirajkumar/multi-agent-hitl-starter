import React, { useState, useEffect } from 'react';
import { Play, Sparkles, Sliders, Cpu, Key, AlertCircle } from 'lucide-react';
import { ProviderInfo, DeliverableType } from '../types';
import { api, StartRunParams } from '../services/api';

interface ConfigurationBarProps {
  onStart: (params: StartRunParams) => void;
  isLoading: boolean;
}

const PRESET_TEMPLATES = [
  {
    title: 'Database Outage Plan',
    type: 'incident_response_plan' as DeliverableType,
    prompt: 'Develop a high-severity Incident Response Plan for an unexpected Redis Sentinel primary failover and cache stampede under peak traffic.',
  },
  {
    title: 'Microservices Architecture Brief',
    type: 'technical_brief' as DeliverableType,
    prompt: 'Author a Technical Brief detailing an event-driven architecture using Kafka, CQRS, and outbox pattern for a payment ledger service.',
  },
  {
    title: 'Multi-Agent Systems Outline',
    type: 'content_outline' as DeliverableType,
    prompt: 'Create a comprehensive technical content outline exploring Stateful Cyclic Multi-Agent Orchestration with LangGraph and HITL gates.',
  },
];

export const ConfigurationBar: React.FC<ConfigurationBarProps> = ({ onStart, isLoading }) => {
  const [task, setTask] = useState('');
  const [deliverableType, setDeliverableType] = useState<DeliverableType>('incident_response_plan');
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('mock');
  const [modelName, setModelName] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  useEffect(() => {
    api.getProviders()
      .then(data => {
        setProviders(data);
        const initial = data.find(p => p.id === 'mock') || data[0];
        if (initial) {
          setSelectedProvider(initial.id);
          setModelName(initial.default_model);
        }
      })
      .catch(err => console.error('Failed to load providers:', err));
  }, []);

  const handleProviderChange = (providerId: string) => {
    setSelectedProvider(providerId);
    const found = providers.find(p => p.id === providerId);
    if (found) {
      setModelName(found.default_model);
    }
  };

  const handleApplyPreset = (preset: typeof PRESET_TEMPLATES[0]) => {
    setTask(preset.prompt);
    setDeliverableType(preset.type);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim()) return;

    onStart({
      task: task.trim(),
      deliverable_type: deliverableType,
      llm_provider: selectedProvider,
      model_name: modelName || undefined,
      temperature,
    });
  };

  const activeProvider = providers.find(p => p.id === selectedProvider);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Top Controls: Type & Provider */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Deliverable Type
              </label>
              <select
                value={deliverableType}
                onChange={e => setDeliverableType(e.target.value as DeliverableType)}
                className="bg-slate-800 border border-slate-700 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500 font-medium"
              >
                <option value="incident_response_plan">Incident Response Plan</option>
                <option value="technical_brief">Technical Brief</option>
                <option value="content_outline">Content Outline</option>
                <option value="architecture_decision_record">Architecture Decision Record (ADR)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
                LLM Provider
              </label>
              <select
                value={selectedProvider}
                onChange={e => handleProviderChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-xs rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500 font-medium"
              >
                {providers.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} {!p.is_configured && p.id !== 'mock' ? '(Key Not Set)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {activeProvider && (
              <div className="hidden sm:flex items-center gap-1.5 mt-5">
                {activeProvider.is_configured ? (
                  <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20" title="Will fallback to Mock provider if invoked">
                    <AlertCircle className="w-3 h-3" />
                    Key Missing (Falls back to Mock)
                  </span>
                )}
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 px-2.5 py-1.5 rounded-lg border border-slate-700 transition"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>{isExpanded ? 'Hide Advanced' : 'Model Settings'}</span>
          </button>
        </div>

        {/* Advanced Settings Drawer */}
        {isExpanded && (
          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Model Name</label>
              <input
                type="text"
                value={modelName}
                onChange={e => setModelName(e.target.value)}
                placeholder="e.g. gpt-4o, claude-3-5-sonnet"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-medium text-slate-300">Temperature</label>
                <span className="text-xs font-mono text-sky-400">{temperature.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={e => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-sky-500"
              />
            </div>
          </div>
        )}

        {/* Prompt Input Box */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-sky-400" />
              Task Objective / Deliverable Prompt
            </label>
          </div>
          <textarea
            rows={3}
            value={task}
            onChange={e => setTask(e.target.value)}
            placeholder="Describe the deliverable requirements, context, and operational constraints for the agents..."
            className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition resize-none font-sans"
          />
        </div>

        {/* Quick Presets & Submit */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-slate-400">Presets:</span>
            {PRESET_TEMPLATES.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleApplyPreset(p)}
                className="text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white px-2.5 py-1 rounded-md border border-slate-700/80 transition"
              >
                {p.title}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading || !task.trim()}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 disabled:opacity-50 disabled:pointer-events-none text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-sky-600/20 transition cursor-pointer"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></span>
                <span>Agents Orchestrating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Launch Workflow</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
