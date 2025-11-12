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
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isWaitingForFirstToken, setIsWaitingForFirstToken] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const previousConversationIdRef = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isWaitingForFirstToken]);

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
    setIsWaitingForFirstToken(true);

    try {
      // Ensure we have a conversation
      const { id: conversationId, isNew } = await ensureConversation();

      // Use streaming mode by default
      let assistantResponseContent = '';
      let assistantMessage: UIMessage | null = null;

      await apiClient.streamMessage(
        conversationId,
        messageContent,
        (event: any) => {
          // Handle first token - replace typing indicator with actual message
          if (event.event === 'reasoning_token' && event.data?.content) {
            if (assistantMessage === null) {
              // First token received - hide typing indicator and create actual message
              setIsWaitingForFirstToken(false);
              
              assistantMessage = {
                id: Date.now() + 1,
                content: event.data.content,
                sender: 'assistant',
                timestamp: new Date(),
                conversationId: conversationId
              };
              
              assistantResponseContent = event.data.content;
              
              setMessages(prev => [
                ...prev.map(msg => 
                  msg.id === userMessage.id 
                    ? { ...msg, conversationId: conversationId }
                    : msg
                ),
                assistantMessage
              ]);
            } else {
              // Subsequent tokens - update existing message
              assistantResponseContent += event.data?.content || '';
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessage!.id 
                    ? { ...msg, content: assistantResponseContent }
                    : msg
                )
              );
            }
          } else if (event.event === 'final_response') {
            // Ensure we capture the final response if streaming tokens weren't complete
            const finalContent = event.data?.response || assistantResponseContent;
            if (finalContent && assistantMessage) {
              assistantResponseContent = finalContent;
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessage!.id 
                    ? { ...msg, content: assistantResponseContent }
                    : msg
                )
              );
            } else if (finalContent && !assistantMessage) {
              // No tokens came through, but we have a final response
              setIsWaitingForFirstToken(false);
              assistantMessage = {
                id: Date.now() + 1,
                content: finalContent,
                sender: 'assistant',
                timestamp: new Date(),
                conversationId: conversationId
              };
              
              setMessages(prev => [
                ...prev.map(msg => 
                  msg.id === userMessage.id 
                    ? { ...msg, conversationId: conversationId }
                    : msg
                ),
                assistantMessage
              ]);
            }
          } else if (event.event === 'error') {
            // Handle streaming errors
            setIsWaitingForFirstToken(false);
            const errorMsg = event.data?.message || 'Error during streaming';
            console.error('Streaming error:', errorMsg);
            
            if (assistantMessage) {
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === assistantMessage!.id 
                    ? { ...msg, content: `Error: ${errorMsg}` }
                    : msg
                )
              );
            } else {
              const errorMessage: UIMessage = {
                id: Date.now() + 1,
                content: `Error: ${errorMsg}`,
                sender: 'assistant',
                timestamp: new Date(),
                conversationId: conversationId
              };
              
              setMessages(prev => [
                ...prev.map(msg => 
                  msg.id === userMessage.id 
                    ? { ...msg, conversationId: conversationId }
                    : msg
                ),
                errorMessage
              ]);
            }
          } else if (event.event === 'debug_end') {
            // Ensure we have some content when debugging ends
            setIsWaitingForFirstToken(false);
            if (!assistantResponseContent.trim() && !assistantMessage) {
              assistantMessage = {
                id: Date.now() + 1,
                content: 'No response content captured during streaming.',
                sender: 'assistant',
                timestamp: new Date(),
                conversationId: conversationId
              };
              
              setMessages(prev => [
                ...prev.map(msg => 
                  msg.id === userMessage.id 
                    ? { ...msg, conversationId: conversationId }
                    : msg
                ),
                assistantMessage
              ]);
            }
          }
        },
        (error: Error) => {
          console.error('Streaming error:', error);
          setIsWaitingForFirstToken(false);
          const errorMessage: UIMessage = {
            id: Date.now() + 2,
            content: `Error: ${error.message}`,
            sender: 'assistant',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
        },
        () => {
          // Streaming complete
          setIsWaitingForFirstToken(false);
        }
      );
      
      // Handle conversation updates
      if (isNew) {
        // New conversation created
        const conversation: Conversation = {
          id: conversationId,
          title: null, // Will be updated later if needed
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        onConversationCreated(conversation);
      } else if (activeConversation) {
        // Existing conversation - always update timestamp
        const updatedConversation: Conversation = {
          ...activeConversation,
          updated_at: new Date().toISOString()
        };
        onConversationUpdated(updatedConversation);
      }

    } catch (error) {
      setIsWaitingForFirstToken(false);
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
            messagesEndRef={messagesEndRef}
            welcomeTitle={getWelcomeTitle()}
            welcomeMessage={getWelcomeMessage()}
            isWaitingForFirstToken={isWaitingForFirstToken}
          />
          <ChatInput 
            value={input}
            onChange={setInput}
            onSend={handleSendMessage}
          />
        </>
      )}
    </div>
  );
}