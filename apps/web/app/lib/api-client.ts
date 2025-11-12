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
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: string;
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
  async sendMessage(conversationId: string, message: string): Promise<ChatResponse> {
    return this.request<ChatResponse>(`/api/v1/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ message } as ChatRequest),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string; service: string }> {
    return this.request<{ status: string; timestamp: string; service: string }>('/health/');
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