import { useState, useEffect, useRef } from "react";
import { ChatMessageList } from "./chat-message-list";
import { ChatInput } from "./chat-input";
import { apiClient, type SessionResponse } from "~/lib/api-client";

export interface Message {
  id: number;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  sessionId?: string;
}

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentSession, setCurrentSession] = useState<SessionResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const connectToSessionStream = (sessionId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = apiClient.createEventStream(sessionId);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status') {
          const statusMessage: Message = {
            id: Date.now(),
            content: `Procesando tu solicitud... Estado: ${data.data.status}`,
            sender: 'assistant',
            timestamp: new Date(),
            sessionId
          };
          setMessages(prev => [...prev, statusMessage]);
        } else if (data.type === 'update') {
          const statusMessage: Message = {
            id: Date.now(),
            content: `Estado: ${data.data.status} - Progreso: ${Math.round(data.data.progress || 0)}%${data.data.stage ? ` - ${data.data.stage}` : ''}`,
            sender: 'assistant',
            timestamp: new Date(),
            sessionId
          };
          setMessages(prev => [...prev, statusMessage]);
        } else if (data.type === 'complete') {
          setIsTyping(false);
          const completionMessage: Message = {
            id: Date.now(),
            content: `Tarea completada con estado: ${data.data.final_status}`,
            sender: 'assistant',
            timestamp: new Date(),
            sessionId
          };
          setMessages(prev => [...prev, completionMessage]);
          eventSource.close();
        } else if (data.type === 'error') {
          setIsTyping(false);
          const errorMessage: Message = {
            id: Date.now(),
            content: `Error: ${data.data.message}`,
            sender: 'assistant',
            timestamp: new Date(),
            sessionId
          };
          setMessages(prev => [...prev, errorMessage]);
          eventSource.close();
        }
      } catch (error) {
        console.error('Error parsing SSE data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      setIsTyping(false);
      eventSource.close();
    };
  };

  const handleSendMessage = async (messageContent: string) => {
    if (!messageContent.trim()) return;
    
    const userMessage: Message = {
      id: Date.now(),
      content: messageContent,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const session = await apiClient.createSession(messageContent);
      setCurrentSession(session);

      const assistantMessage: Message = {
        id: Date.now() + 1,
        content: `Perfecto! He creado una nueva sesión (${session.id.substring(0, 8)}...) para procesar tu solicitud. Te mantendré informado del progreso.`,
        sender: 'assistant',
        timestamp: new Date(),
        sessionId: session.id
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      connectToSessionStream(session.id);
    } catch (error) {
      setIsTyping(false);
      const errorMessage: Message = {
        id: Date.now() + 2,
        content: `Error: ${error instanceof Error ? error.message : 'No se pudo conectar con el agente'}`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <ChatMessageList 
        messages={messages} 
        isTyping={isTyping}
        messagesEndRef={messagesEndRef} 
      />
      <ChatInput 
        value={input}
        onChange={setInput}
        onSend={handleSendMessage}
      />
    </div>
  );
}