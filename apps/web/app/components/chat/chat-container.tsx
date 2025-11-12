import { useState, useEffect, useRef } from "react";
import { ChatMessageList } from "./chat-message-list";
import { ChatInput } from "./chat-input";
import { apiClient, type UIMessage, type Conversation } from "~/lib/api-client";

interface ChatContainerProps {
  activeConversation: Conversation | null;
  onConversationCreated: (conversation: Conversation) => void;
  onConversationUpdated: (conversation: Conversation) => void;
}

export function ChatContainer({
  activeConversation,
  onConversationCreated,
  onConversationUpdated,
}: ChatContainerProps) {
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const previousConversationIdRef = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load messages when active conversation changes
  useEffect(() => {
    const currentConversationId = activeConversation?.id || null;
    const previousConversationId = previousConversationIdRef.current;
    
    if (activeConversation) {
      // Only load messages if this is a different conversation than before
      // This prevents loading when a new conversation is created during message flow
      if (currentConversationId !== previousConversationId && previousConversationId !== null) {
        loadConversationMessages(activeConversation.id);
      }
    } else {
      setMessages([]);
    }
    
    previousConversationIdRef.current = currentConversationId;
  }, [activeConversation]);

  const loadConversationMessages = async (conversationId: string) => {
    try {
      setIsLoadingMessages(true);
      const conversation = await apiClient.getConversation(conversationId);
      
      const uiMessages = conversation.messages.map(msg => 
        apiClient.formatMessageForUI(msg, conversationId)
      );
      
      setMessages(uiMessages);
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessages([]);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const ensureConversation = async (): Promise<{ id: string; isNew: boolean }> => {
    if (activeConversation) {
      return { id: activeConversation.id, isNew: false };
    }

    try {
      const conversation = await apiClient.createConversation();
      // Don't notify about creation yet - wait until after message is sent
      return { id: conversation.id, isNew: true };
    } catch (error) {
      throw new Error(`No se pudo crear la conversación: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    }
  };

  const handleSendMessage = async (messageContent: string) => {
    if (!messageContent.trim()) return;
    
    // Add user message to UI immediately
    const userMessage: UIMessage = {
      id: Date.now(),
      content: messageContent,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      // Ensure we have a conversation
      const { id: conversationId, isNew } = await ensureConversation();

      // Send message to API
      const response = await apiClient.sendMessage(conversationId, messageContent);

      // Add assistant response
      const assistantMessage: UIMessage = {
        id: Date.now() + 1,
        content: response.response,
        sender: 'assistant',
        timestamp: new Date(),
        conversationId: response.conversation_id
      };
      
      // Update user message to include conversation ID and add assistant response
      setMessages(prev => [
        ...prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, conversationId: response.conversation_id }
            : msg
        ),
        assistantMessage
      ]);
      
      // If this was a new conversation, now notify about its creation
      if (isNew) {
        const conversation: Conversation = {
          id: conversationId,
          title: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        onConversationCreated(conversation);
      } else {
        // Update existing conversation timestamp
        if (activeConversation) {
          const updatedConversation: Conversation = {
            ...activeConversation,
            updated_at: new Date().toISOString()
          };
          onConversationUpdated(updatedConversation);
        }
      }
      
      setIsTyping(false);

    } catch (error) {
      setIsTyping(false);
      const errorMessage: UIMessage = {
        id: Date.now() + 2,
        content: `Error: ${error instanceof Error ? error.message : 'No se pudo enviar el mensaje'}`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const getWelcomeTitle = () => {
    if (activeConversation) {
      return activeConversation.title || 'Conversación';
    }
    return 'Chat Assistant';
  };

  const getWelcomeMessage = () => {
    if (activeConversation) {
      return 'Continúa tu conversación';
    }
    return '¿En qué puedo ayudarte hoy?';
  };

  return (
    <div className="flex flex-col h-screen">
      {isLoadingMessages ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600 mx-auto mb-4"></div>
            <p className="text-sky-600">Cargando conversación...</p>
          </div>
        </div>
      ) : (
        <>
          <ChatMessageList 
            messages={messages} 
            isTyping={isTyping}
            messagesEndRef={messagesEndRef}
            welcomeTitle={getWelcomeTitle()}
            welcomeMessage={getWelcomeMessage()}
          />
          <ChatInput 
            value={input}
            onChange={setInput}
            onSend={handleSendMessage}
            disabled={isTyping}
          />
        </>
      )}
    </div>
  );
}