import { useState, useEffect, useRef, useCallback } from 'react';
import { WorkflowState, AgentNodeName, InterruptData, WorkflowEvent } from '../types';
import { api, StartRunParams, ResumeParams } from '../services/api';

const STORAGE_KEY = 'multi_agent_thread_id';

const initialState: WorkflowState = {
  thread_id: null,
  status: 'idle',
  currentNode: null,
  plan: [],
  researchData: [],
  draft: '',
  critique: null,
  revisionCount: 0,
  finalOutput: null,
  isInterrupted: false,
  interruptData: null,
  events: [],
  error: null,
};

export function useAgentStream() {
  const [state, setState] = useState<WorkflowState>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? { ...initialState, thread_id: saved } : initialState;
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  // Clean up existing SSE connection
  const closeStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Connect to SSE stream for a thread
  const connectToStream = useCallback((threadId: string) => {
    closeStream();

    const es = new EventSource(`/api/runs/${threadId}/stream`);
    eventSourceRef.current = es;

    es.addEventListener('run_started', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setState(prev => ({
        ...prev,
        status: 'running',
        currentNode: 'supervisor',
        events: [
          ...prev.events,
          { node: 'system', action: 'started', timestamp: data.timestamp, detail: 'Workflow initiated.' },
        ],
      }));
    });

    es.addEventListener('node_finish', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      const nodeName = data.node as AgentNodeName;
      const update = data.update || {};

      setState(prev => {
        const nextNode =
          nodeName === 'supervisor'
            ? (update.next_agent as AgentNodeName) || prev.currentNode
            : nodeName;

        return {
          ...prev,
          currentNode: nextNode,
          plan: update.plan ? update.plan : prev.plan,
          researchData: update.research_data ? update.research_data : prev.researchData,
          draft: update.draft !== undefined ? update.draft : prev.draft,
          critique: update.critique !== undefined ? update.critique : prev.critique,
          revisionCount: update.revision_count !== undefined ? update.revision_count : prev.revisionCount,
          finalOutput: update.final_output !== undefined ? update.final_output : prev.finalOutput,
          events: update.events ? [...prev.events, ...update.events] : prev.events,
        };
      });
    });

    es.addEventListener('interrupt', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setState(prev => ({
        ...prev,
        status: 'interrupted',
        currentNode: 'human_review',
        isInterrupted: true,
        interruptData: data.interrupt_data as InterruptData,
        draft: data.draft || prev.draft,
        revisionCount: data.revision_count !== undefined ? data.revision_count : prev.revisionCount,
        events: [
          ...prev.events,
          {
            node: 'human_review',
            action: 'interrupted',
            timestamp: data.timestamp,
            detail: 'Execution halted at Human-in-the-Loop review gate.',
          },
        ],
      }));
    });

    es.addEventListener('complete', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setState(prev => ({
        ...prev,
        status: 'completed',
        currentNode: 'publisher',
        isInterrupted: false,
        finalOutput: data.final_output || prev.draft,
        events: [
          ...prev.events,
          {
            node: 'publisher',
            action: 'complete',
            timestamp: data.timestamp,
            detail: 'Workflow completed successfully.',
          },
        ],
      }));
      closeStream();
    });

    es.addEventListener('error', (e: any) => {
      // EventSource generic error or server-emitted error
      if (e.data) {
        try {
          const data = JSON.parse(e.data);
          setState(prev => ({ ...prev, error: data.error, status: 'error' }));
        } catch {
          // Keepalive or connection reconnect attempt
        }
      }
    });

    return () => closeStream();
  }, [closeStream]);

  // Restore state on mount if thread_id is stored
  useEffect(() => {
    const threadId = state.thread_id;
    if (threadId && state.status === 'idle') {
      api.getRunState(threadId)
        .then(data => {
          if (data && data.status !== 'not_started') {
            setState(prev => ({
              ...prev,
              thread_id: threadId,
              status: data.is_interrupted ? 'interrupted' : (data.status as any),
              isInterrupted: data.is_interrupted,
              interruptData: data.interrupt_data,
              draft: data.draft || '',
              finalOutput: data.final_output,
              plan: data.plan || [],
              researchData: data.research_data || [],
              revisionCount: data.revision_count || 0,
              events: data.events || [],
              currentNode: data.is_interrupted ? 'human_review' : null,
            }));

            // If it's still running, reconnect to stream
            if (data.status === 'running') {
              connectToStream(threadId);
            }
          }
        })
        .catch(err => {
          console.warn('Failed to restore saved thread:', err);
          localStorage.removeItem(STORAGE_KEY);
        });
    }

    return () => closeStream();
  }, [connectToStream, closeStream]);

  // Start new run
  const startRun = async (params: StartRunParams) => {
    setState({ ...initialState, status: 'running' });
    try {
      const res = await api.startRun(params);
      localStorage.setItem(STORAGE_KEY, res.thread_id);
      setState(prev => ({
        ...prev,
        thread_id: res.thread_id,
        status: 'running',
        currentNode: 'supervisor',
      }));
      connectToStream(res.thread_id);
    } catch (err: any) {
      setState(prev => ({ ...prev, status: 'error', error: err.message }));
    }
  };

  // Submit HITL resume action
  const resumeRun = async (params: ResumeParams) => {
    if (!state.thread_id) return;
    setState(prev => ({ ...prev, status: 'resuming', isInterrupted: false }));

    try {
      await api.resumeRun(state.thread_id, params);
      // Keep or re-establish stream listener to capture subsequent nodes
      connectToStream(state.thread_id);
    } catch (err: any) {
      setState(prev => ({ ...prev, status: 'error', error: err.message }));
    }
  };

  // Reset workflow
  const resetRun = () => {
    closeStream();
    localStorage.removeItem(STORAGE_KEY);
    setState(initialState);
  };

  return {
    state,
    startRun,
    resumeRun,
    resetRun,
  };
}
