import { useState, useEffect } from "react";
import { ChatContainer } from "./chat-container";
import { ConversationsSidebar } from "./conversations-sidebar";
import { apiClient, type Conversation } from "~/lib/api-client";

export function ChatLayout() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setIsLoadingConversations(true);
      const fetchedConversations = await apiClient.getConversations(50);
      setConversations(fetchedConversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setActiveConversation(conversation);
  };

  const handleNewConversation = () => {
    setActiveConversation(null);
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await apiClient.deleteConversation(conversationId);
      
      // Remove from list
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      // If this was the active conversation, clear it
      if (activeConversation?.id === conversationId) {
        setActiveConversation(null);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      
      // Show user-friendly error message
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Error al eliminar la conversación. Por favor, inténtalo de nuevo.';
      
      // You can replace this with a toast notification system
      alert(`Error: ${errorMessage}`);
    }
  };

  // Called when a new conversation is created in ChatContainer
  const handleConversationCreated = (conversation: Conversation) => {
    setConversations(prev => [conversation, ...prev]);
    setActiveConversation(conversation);
  };

  // Called when conversation is updated (new messages)
  const handleConversationUpdated = (conversation: Conversation) => {
    setConversations(prev => 
      prev.map(conv => 
        conv.id === conversation.id 
          ? { ...conv, updated_at: conversation.updated_at }
          : conv
      )
    );
    
    // Also update active conversation if it's the same one
    if (activeConversation?.id === conversation.id) {
      setActiveConversation(prev => prev ? { ...prev, updated_at: conversation.updated_at } : null);
    }
  };


  return (
    <div className="flex h-screen">
      <ConversationsSidebar
        conversations={conversations}
        activeConversationId={activeConversation?.id}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isLoading={isLoadingConversations}
        open={sidebarOpen}
        onOpenChange={setSidebarOpen}
      />
      
      <div 
        className={`flex-1 transition-all duration-300 ease-in-out ${
          sidebarOpen ? 'lg:ml-80' : ''
        }`}
      >
        <ChatContainer
          activeConversation={activeConversation}
          onConversationCreated={handleConversationCreated}
          onConversationUpdated={handleConversationUpdated}
        />
      </div>
    </div>
  );
}