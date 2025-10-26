/**
 * Frontend API Service
 * TypeScript client for Paralegal AI Backend API
 * 
 * Connects React frontend to FastAPI backend (port 8080)
 */

/**
 * API Service Layer
 * Connects React frontend to FastAPI backend (port 9081 via SSH tunnel)
 */

// Use environment variable or default to localhost via SSH tunnel
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:9081';

// ============================================================================
// TYPE DEFINITIONS (matching backend Pydantic models)
// ============================================================================

export interface Task {
  id: string;
  status: 'pending' | 'processing' | 'awaiting_approval' | 'approved' | 'sent' | 'failed' | 'rejected';
  source: 'email' | 'text' | 'call';
  content: string;
  sender?: string;
  subject?: string;
  priority: 'low' | 'medium' | 'high';
  assigned_agent?: string;
  ai_response?: string;
  approved_response?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface IncomingTask {
  source: 'email' | 'text' | 'call';
  content: string;
  sender?: string;
  subject?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface TaskApproval {
  approved: boolean;
  edited_content?: string;
  send_immediately?: boolean;
}

export interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'processing' | 'error';
  tasks_processed: number;
  success_rate: number;
  avg_response_time: number;
  current_task?: string;
}

export interface SystemStats {
  total_tasks: number;
  tasks_pending: number;
  tasks_processing: number;
  tasks_awaiting_approval: number;
  tasks_completed: number;
  total_agents: number;
  active_agents: number;
  avg_processing_time: number;
  success_rate: number;
  cases_scraped_today: number;
  scraping_speed: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  vllm_connected: boolean;
  intelligent_scraper: boolean;
  agents_initialized: number;
  timestamp: string;
}

// ============================================================================
// API CLIENT CLASS
// ============================================================================

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class ParalegalAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      // Network or parsing error
      console.error('API Request failed:', error);
      throw new APIError(
        error instanceof Error ? error.message : 'Unknown error occurred'
      );
    }
  }

  // ============================================================================
  // HEALTH & STATUS
  // ============================================================================

  async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getRoot(): Promise<any> {
    return this.request<any>('/');
  }

  // ============================================================================
  // TASKS
  // ============================================================================

  async getTasks(filters?: { status?: Task['status'] }): Promise<Task[]> {
    const params = new URLSearchParams();
    if (filters?.status) {
      params.append('status', filters.status);
    }
    
    const query = params.toString();
    return this.request<Task[]>(`/tasks${query ? `?${query}` : ''}`);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>(`/tasks/${taskId}`);
  }

  async ingestTask(taskData: IncomingTask): Promise<{ task_id: string; status: string; message: string }> {
    return this.request<{ task_id: string; status: string; message: string }>('/tasks/ingest', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  async approveTask(
    taskId: string,
    approval: TaskApproval
  ): Promise<{ task_id: string; status: string; message: string }> {
    return this.request<{ task_id: string; status: string; message: string }>(
      `/tasks/${taskId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(approval),
      }
    );
  }

  // ============================================================================
  // AGENTS
  // ============================================================================

  async getAgents(): Promise<Agent[]> {
    return this.request<Agent[]>('/agents');
  }

  async getAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>(`/agents/${agentId}`);
  }

  // ============================================================================
  // STATISTICS
  // ============================================================================

  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>('/stats');
  }
}

// ============================================================================
// EXPORT SINGLETON INSTANCE
// ============================================================================

export const api = new ParalegalAPI();

// ============================================================================
// CONVENIENCE FUNCTIONS (for easier imports)
// ============================================================================

export const checkHealth = () => api.checkHealth();
export const getTasks = (filters?: { status?: Task['status'] }) => api.getTasks(filters);
export const getTask = (taskId: string) => api.getTask(taskId);
export const ingestTask = (taskData: IncomingTask) => api.ingestTask(taskData);
export const approveTask = (taskId: string, approval: TaskApproval) => api.approveTask(taskId, approval);
export const getAgents = () => api.getAgents();
export const getAgent = (agentId: string) => api.getAgent(agentId);
export const getSystemStats = () => api.getSystemStats();

// ============================================================================
// POLLING UTILITIES
// ============================================================================

/**
 * Poll for tasks with automatic refresh
 * Returns a cleanup function to stop polling
 */
export function pollTasks(
  callback: (tasks: Task[]) => void,
  intervalMs: number = 5000,
  filters?: { status?: Task['status'] }
): () => void {
  let intervalId: number;

  const poll = async () => {
    try {
      const tasks = await getTasks(filters);
      callback(tasks);
    } catch (error) {
      console.error('Failed to poll tasks:', error);
    }
  };

  // Initial poll
  poll();

  // Set up interval
  intervalId = window.setInterval(poll, intervalMs);

  // Return cleanup function
  return () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}

/**
 * Poll for system stats with automatic refresh
 */
export function pollStats(
  callback: (stats: SystemStats) => void,
  intervalMs: number = 10000
): () => void {
  let intervalId: number;

  const poll = async () => {
    try {
      const stats = await getSystemStats();
      callback(stats);
    } catch (error) {
      console.error('Failed to poll stats:', error);
    }
  };

  poll();
  intervalId = window.setInterval(poll, intervalMs);

  return () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}

/**
 * Poll for agents with automatic refresh
 */
export function pollAgents(
  callback: (agents: Agent[]) => void,
  intervalMs: number = 5000
): () => void {
  let intervalId: number;

  const poll = async () => {
    try {
      const agents = await getAgents();
      callback(agents);
    } catch (error) {
      console.error('Failed to poll agents:', error);
    }
  };

  poll();
  intervalId = window.setInterval(poll, intervalMs);

  return () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  };
}

// ============================================================================
// DEMO/TESTING UTILITIES
// ============================================================================

/**
 * Generate sample task for testing
 */
export async function createSampleTask(): Promise<{ task_id: string; status: string; message: string }> {
  const sampleTasks: IncomingTask[] = [
    {
      source: 'email',
      content: 'I was in a car accident last week and injured my back. The other driver ran a red light. What should I do?',
      sender: 'john.doe@example.com',
      subject: 'Car accident - need help',
      priority: 'high'
    },
    {
      source: 'text',
      content: 'Can you find cases similar to mine? Slip and fall at grocery store, broken wrist.',
      sender: '+1234567890',
      priority: 'medium'
    },
    {
      source: 'call',
      content: 'Medical malpractice case - doctor misdiagnosed condition leading to complications. Need settlement estimate.',
      sender: 'Jane Smith',
      priority: 'high'
    },
  ];

  const randomTask = sampleTasks[Math.floor(Math.random() * sampleTasks.length)];
  return ingestTask(randomTask);
}

/**
 * Test API connection
 */
export async function testConnection(): Promise<boolean> {
  try {
    const health = await checkHealth();
    console.log('API Health Check:', health);
    return health.status === 'healthy' || health.status === 'degraded';
  } catch (error) {
    console.error('API Connection failed:', error);
    return false;
  }
}

export default api;
