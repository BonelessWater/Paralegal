import { Task, Agent, OutreachActivity, SystemStats, TaskType, AgentType } from './types';

// Mock data for demonstration

export const mockTasks: Task[] = [
  {
    id: '1',
    source: 'email',
    type: 'client_communication',
    content: 'Hi, um, I wanted to check on my case... The insurance company is saying they wont pay for my medical bills??? Can you help me understand what\'s going on? I\'m really worried about this...',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    status: 'awaiting_approval',
    assignedAgent: 'communicator',
    aiDraft: 'Dear Client,\n\nThank you for reaching out. I understand your concern regarding the insurance company\'s position on your medical bills. This is a common tactic, and we\'re here to help navigate this situation.\n\nWe\'re currently reviewing your policy coverage and will be sending a formal demand letter to the insurance company. Rest assured, we have extensive experience handling these disputes, and we\'re committed to securing the coverage you\'re entitled to.\n\nI\'ll schedule a call with you this week to discuss our strategy in detail. In the meantime, please don\'t worry - you\'re in good hands.\n\nBest regards,\n[Attorney Name]',
    clientName: 'Sarah Johnson',
    priority: 'high'
  },
  {
    id: '2',
    source: 'text',
    type: 'scheduling',
    content: 'hey when is my deposition again? cant remember if its next week or the week after',
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    status: 'processing',
    assignedAgent: 'scheduler',
    clientName: 'Mike Chen',
    priority: 'medium'
  },
  {
    id: '3',
    source: 'call',
    type: 'records_request',
    content: 'Call Transcript: "Yeah, so, uh, the hospital said they don\'t have my X-rays from the ER visit. And like, the physical therapy place also said they\'re missing some paperwork. I don\'t know what to do about this..."',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    status: 'awaiting_approval',
    assignedAgent: 'records_wrangler',
    aiDraft: 'MEDICAL RECORDS REQUEST\n\nTo: St. Mary\'s Hospital Medical Records Department\nRe: Patient Sarah Johnson, DOB: 05/12/1985\n\nDear Records Coordinator,\n\nWe represent Ms. Sarah Johnson in a personal injury matter. Please provide certified copies of the following records from her emergency room visit on October 15, 2025:\n\n- All X-ray images and radiologist reports\n- Emergency department treatment notes\n- Nursing notes and vital signs\n- Discharge summary and instructions\n\nAdditionally, we request physical therapy records from Atlantic PT Clinic for the period of October 20-25, 2025.\n\nPlease contact our office if you require additional authorization. We appreciate your prompt attention to this matter.\n\nSincerely,\n[Law Firm Name]',
    clientName: 'Sarah Johnson',
    priority: 'high'
  },
  {
    id: '4',
    source: 'email',
    type: 'legal_research',
    content: 'Need case law for slip and fall at grocery store - wet floor, no sign posted. Client has herniated disc. Looking for settlement range in Georgia jurisdiction.',
    timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    status: 'processing',
    assignedAgent: 'legal_researcher',
    clientName: 'Internal Request',
    priority: 'medium'
  },
  {
    id: '5',
    source: 'email',
    type: 'evidence_sorting',
    content: '[Email with 5 attachments: medical_bill_1.pdf, medical_bill_2.pdf, police_report.pdf, witness_statement.docx, insurance_letter.pdf]',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    status: 'pending',
    clientName: 'David Martinez',
    priority: 'low'
  }
];

export const mockAgents: Agent[] = [
  {
    id: 'communicator',
    name: 'Client Communication Guru',
    description: 'Transforms messy client messages into empathetic, professional responses',
    icon: '💬',
    activeTasksCount: 3,
    completedToday: 12,
    avgProcessingTime: 45
  },
  {
    id: 'records_wrangler',
    name: 'Records Wrangler',
    description: 'Generates formal medical records requests and tracks missing documents',
    icon: '📋',
    activeTasksCount: 2,
    completedToday: 8,
    avgProcessingTime: 60
  },
  {
    id: 'legal_researcher',
    name: 'Legal Researcher',
    description: 'Uses RAG to find precedents and suggest settlement ranges',
    icon: '⚖️',
    activeTasksCount: 1,
    completedToday: 5,
    avgProcessingTime: 180
  },
  {
    id: 'evidence_sorter',
    name: 'Evidence Sorter',
    description: 'Categorizes documents and extracts key information via OCR',
    icon: '📁',
    activeTasksCount: 1,
    completedToday: 15,
    avgProcessingTime: 30
  },
  {
    id: 'scheduler',
    name: 'Voice Bot Scheduler',
    description: 'Manages depositions and client appointments via voice and text',
    icon: '📅',
    activeTasksCount: 2,
    completedToday: 7,
    avgProcessingTime: 40
  }
];

export const mockOutreach: OutreachActivity[] = [
  {
    id: '1',
    taskId: '1',
    type: 'email',
    recipient: 'sarah.johnson@email.com',
    content: 'Dear Client, Thank you for reaching out...',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    status: 'delivered'
  },
  {
    id: '2',
    taskId: '2',
    type: 'sms',
    recipient: '+1-555-0123',
    content: 'Hi Mike, your deposition is scheduled for Nov 5 at 2pm. Reply YES to confirm.',
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    status: 'delivered'
  },
  {
    id: '3',
    taskId: '3',
    type: 'voice',
    recipient: '+1-555-0456',
    content: 'Hi Sarah, this is a reminder about your physical therapy appointment tomorrow at 10am...',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    status: 'sent'
  }
];

export const mockStats: SystemStats = {
  totalTasksToday: 47,
  pendingApproval: 3,
  completed: 42,
  avgResponseTime: 52,
  amdInferenceSpeed: 127,
  activeAgents: 5
};

// Helper functions
export const getTaskTypeColor = (type: TaskType | undefined): string => {
  const colors: Record<TaskType, string> = {
    client_communication: 'bg-primary-100 text-primary-800 border border-primary-300',
    records_request: 'bg-bronze-100 text-bronze-800 border border-bronze-300',
    legal_research: 'bg-navy-100 text-navy-800 border border-navy-300',
    scheduling: 'bg-emerald-100 text-emerald-800 border border-emerald-300',
    evidence_sorting: 'bg-primary-50 text-primary-700 border border-primary-200'
  };
  return type ? colors[type] : 'bg-marble-100 text-marble-800 border border-marble-300';
};

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-marble-200 text-marble-800 border border-marble-400',
    processing: 'bg-bronze-100 text-bronze-800 border border-bronze-300',
    awaiting_approval: 'bg-primary-100 text-primary-800 border border-primary-400',
    approved: 'bg-emerald-100 text-emerald-800 border border-emerald-400',
    sent: 'bg-navy-100 text-navy-800 border border-navy-300',
    rejected: 'bg-red-100 text-red-800 border border-red-300'
  };
  return colors[status] || 'bg-marble-100 text-marble-800 border border-marble-300';
};

export const getAgentByType = (type: AgentType): Agent | undefined => {
  return mockAgents.find(agent => agent.id === type);
};
