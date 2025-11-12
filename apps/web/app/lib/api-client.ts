// Types based on the Chat Agent API
export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface CreateConversationRequest {
  title?: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  title_updated: boolean;
  new_title?: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: string;
}

// Tramites-specific types
export interface TramiteSession {
  session_id: string;
  conversation_id: string;
  tramite_type: string;
  current_phase: string;
  completion_percentage: number;
  is_completed: boolean;
  created_at: string;
}

export interface TramiteSessionDetail extends TramiteSession {
  user_profile?: Record<string, any>;
  validated_documents: Record<string, any>[];
  checklist: Record<string, any>[];
  updated_at?: string;
}

export interface ValidationResponse {
  is_valid: boolean;
  confidence_score: number;
  confidence_level: string;
  extracted_data: Record<string, any>;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export interface CreateTramiteSessionRequest {
  tramite_type: string;
  conversation_id?: string;
}

export interface ValidateCurpRequest {
  curp: string;
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
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData: ErrorResponse = await response.json().catch(() => ({
        error: 'HTTP_ERROR',
        message: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Conversation management
  async createConversation(title?: string): Promise<Conversation> {
    return this.request<Conversation>('/api/v1/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title } as CreateConversationRequest),
    });
  }

  async getConversations(limit: number = 20): Promise<Conversation[]> {
    return this.request<Conversation[]>(`/api/v1/chat/conversations?limit=${limit}`);
  }

  async getConversation(conversationId: string): Promise<ConversationDetail> {
    return this.request<ConversationDetail>(`/api/v1/chat/conversations/${conversationId}`);
  }

  async deleteConversation(conversationId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/chat/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  // Chat functionality
  async sendMessage(conversationId: string, message: string, useTramitesAgent = false): Promise<ChatResponse> {
    // If using tramites agent, create a tramite session first if needed
    if (useTramitesAgent) {
      try {
        // Try to create a tramite session linked to this conversation
        await this.createTramiteSession({
          tramite_type: "SAT_RFC_INSCRIPCION_PF", // Default to RFC registration
          conversation_id: conversationId
        });
      } catch (error) {
        // Session might already exist, continue anyway
        console.log('Tramite session may already exist, continuing...');
      }
    }
    
    return this.request<ChatResponse>(`/api/v1/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ message } as ChatRequest),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string; service: string }> {
    return this.request<{ status: string; timestamp: string; service: string }>('/health/');
  }

  // Tramites endpoints
  async createTramiteSession(request: CreateTramiteSessionRequest): Promise<TramiteSession> {
    return this.request<TramiteSession>('/api/v1/tramites/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTramiteSession(sessionId: string): Promise<TramiteSessionDetail> {
    return this.request<TramiteSessionDetail>(`/api/v1/tramites/sessions/${sessionId}`);
  }

  async validateCurp(sessionId: string, request: ValidateCurpRequest): Promise<ValidationResponse> {
    return this.request<ValidationResponse>(`/api/v1/tramites/sessions/${sessionId}/validate-curp`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async deleteTramiteSession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/tramites/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Format message for UI
  formatMessageForUI(message: Message, conversationId: string): UIMessage {
    return {
      id: message.id,
      content: message.content,
      sender: message.role,
      timestamp: new Date(message.created_at),
      conversationId
    };
  }
}

// UI-specific message interface
export interface UIMessage {
  id: number;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  conversationId?: string;
}

export const apiClient = new ApiClient();