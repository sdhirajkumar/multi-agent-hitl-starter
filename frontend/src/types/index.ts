export type DeliverableType =
  | 'incident_response_plan'
  | 'technical_brief'
  | 'content_outline'
  | 'architecture_decision_record';

export type AgentNodeName =
  | 'supervisor'
  | 'researcher'
  | 'writer'
  | 'reviewer'
  | 'human_review'
  | 'publisher';

export type WorkflowStatus =
  | 'idle'
  | 'running'
  | 'interrupted'
  | 'resuming'
  | 'completed'
  | 'error';

export interface ProviderInfo {
  id: string;
  name: string;
  default_model: string;
  models: string[];
  is_configured: boolean;
  is_local: boolean;
}

export interface InterruptData {
  type: string;
  task: string;
  deliverable_type: string;
  draft: string;
  revision_count: number;
  critique: string;
  timestamp: string;
}

export interface WorkflowEvent {
  node?: string;
  agent?: string;
  action?: string;
  timestamp: string;
  detail?: string;
  revision?: number;
  [key: string]: any;
}

export interface WorkflowState {
  thread_id: string | null;
  status: WorkflowStatus;
  currentNode: AgentNodeName | null;
  plan: string[];
  researchData: string[];
  draft: string;
  critique: string | null;
  revisionCount: number;
  finalOutput: string | null;
  isInterrupted: boolean;
  interruptData: InterruptData | null;
  events: WorkflowEvent[];
  error: string | null;
}
