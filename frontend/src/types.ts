export type TaskStatus = 'pending' | 'processing' | 'awaiting_approval' | 'approved' | 'sent' | 'rejected';
export type TaskSource = 'email' | 'text' | 'call';
export type TaskType = 'client_communication' | 'records_request' | 'legal_research' | 'scheduling' | 'evidence_sorting';
export type AgentType = 'communicator' | 'records_wrangler' | 'legal_researcher' | 'evidence_sorter' | 'scheduler';

export interface Task {
  id: string;
  source: TaskSource;
  type?: TaskType;
  content: string;
  timestamp: string;
  status: TaskStatus;
  assignedAgent?: AgentType;
  aiDraft?: string;
  humanEdits?: string;
  outreachType?: 'email' | 'sms' | 'voice';
  clientName?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface Agent {
  id: AgentType;
  name: string;
  description: string;
  icon: string;
  activeTasksCount: number;
  completedToday: number;
  avgProcessingTime: number;
}

export interface OutreachActivity {
  id: string;
  taskId: string;
  type: 'email' | 'sms' | 'voice';
  recipient: string;
  content: string;
  timestamp: string;
  status: 'sent' | 'delivered' | 'failed';
}

export interface SystemStats {
  totalTasksToday: number;
  pendingApproval: number;
  completed: number;
  avgResponseTime: number;
  amdInferenceSpeed: number;
  activeAgents: number;
}
