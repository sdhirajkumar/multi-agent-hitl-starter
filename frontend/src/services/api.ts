import { ProviderInfo, WorkflowState, InterruptData } from '../types';

const API_BASE = '/api';

export interface StartRunParams {
  task: string;
  deliverable_type: string;
  llm_provider?: string;
  model_name?: string;
  temperature?: number;
}

export interface ResumeParams {
  action: 'approve' | 'edit' | 'reject';
  edited_draft?: string;
  feedback?: string;
}

export const api = {
  async getProviders(): Promise<ProviderInfo[]> {
    const res = await fetch(`${API_BASE}/providers`);
    if (!res.ok) throw new Error('Failed to fetch providers');
    return res.json();
  },

  async startRun(params: StartRunParams): Promise<{ thread_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/runs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to start run');
    }
    return res.json();
  },

  async resumeRun(threadId: string, params: ResumeParams): Promise<any> {
    const res = await fetch(`${API_BASE}/runs/${threadId}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to resume run');
    }
    return res.json();
  },

  async getRunState(threadId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/runs/${threadId}/state`);
    if (!res.ok) throw new Error('Failed to fetch run state');
    return res.json();
  },
};
