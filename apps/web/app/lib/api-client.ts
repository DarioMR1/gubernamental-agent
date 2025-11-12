export interface Message {
  id: number;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

export interface CreateSessionRequest {
  instruction: string;
  priority?: number;
}

export interface SessionResponse {
  id: string;
  instruction: string;
  status: 'active' | 'completed' | 'failed' | 'requires_approval' | 'aborted' | 'pending' | 'running' | 'paused';
  stage?: string;
  priority: number;
  progress_percentage: number;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  metadata?: Record<string, any>;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
    request_id?: string;
  };
}

class ApiClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor() {
    this.baseUrl = 'http://localhost:8000';
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || `HTTP ${response.status}`);
    }

    return data;
  }

  async createSession(instruction: string): Promise<SessionResponse> {
    const response = await this.request<SessionResponse>('/v1/sessions', {
      method: 'POST',
      body: JSON.stringify({
        instruction,
        priority: 3
      } as CreateSessionRequest),
    });

    return response.data;
  }

  async getSession(sessionId: string): Promise<SessionResponse> {
    const response = await this.request<SessionResponse>(`/v1/sessions/${sessionId}`);
    return response.data;
  }

  async getSessionHistory(sessionId: string): Promise<any[]> {
    const response = await this.request<any[]>(`/v1/sessions/${sessionId}/history`);
    return response.data;
  }

  async abortSession(sessionId: string): Promise<boolean> {
    const response = await this.request<{ success: boolean }>(`/v1/sessions/${sessionId}/abort`, {
      method: 'POST',
    });
    return response.data.success;
  }

  createEventStream(sessionId: string): EventSource {
    return new EventSource(`${this.baseUrl}/v1/sessions/${sessionId}/stream`);
  }
}

export const apiClient = new ApiClient();