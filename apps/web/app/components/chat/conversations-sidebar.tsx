import { useState, useEffect } from "react";
import { Plus, MessageSquare, Trash2, X } from "lucide-react";
import { Button } from "~/components/ui/button";
import { ScrollArea } from "~/components/ui/scroll-area";
import { cn } from "~/lib/utils";
import { type Conversation } from "~/lib/api-client";

interface ConversationsSidebarProps {
  conversations: Conversation[];
  activeConversationId?: string;
  onSelectConversation: (conversation: Conversation) => void;
  onNewConversation: () => void;
  onDeleteConversation: (conversationId: string) => void;
  isLoading?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function ConversationsSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isLoading = false,
  open: controlledOpen,
  onOpenChange,
}: ConversationsSidebarProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [isLargeScreen, setIsLargeScreen] = useState(false);
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;

  useEffect(() => {
    const checkScreenSize = () => {
      setIsLargeScreen(window.innerWidth >= 1024); // lg breakpoint
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return date.toLocaleTimeString('es-ES', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else if (diffInDays < 7) {
      return date.toLocaleDateString('es-ES', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('es-ES', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  return (
    <>
      {/* Trigger Button */}
      {!open && (
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-4 left-4 z-30 backdrop-blur-md bg-white/60 border border-white/30 text-sky-700 hover:bg-white/70 hover:text-sky-800 transition-all"
          onClick={() => setOpen(!open)}
        >
          <MessageSquare className="h-5 w-5" />
        </Button>
      )}

      {/* Mobile Overlay */}
      {open && !isLargeScreen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar Panel */}
      <div
        className={cn(
          "fixed top-0 left-0 h-full w-80 z-40 backdrop-blur-md bg-white/90 border-r border-white/30",
          "transform transition-transform duration-300 ease-in-out",
          "flex flex-col",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="p-6 pb-4 flex items-center justify-between">
          <h2 className="text-sky-700 font-semibold text-lg">
            Conversaciones
          </h2>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-sky-600 hover:text-sky-800"
            onClick={() => setOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        {/* New Conversation Button */}
        <div className="px-6 pb-4">
          <Button
            onClick={() => {
              onNewConversation();
              if (!isLargeScreen) {
                setOpen(false);
              }
            }}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nueva conversación
          </Button>
        </div>

        {/* Conversations List */}
        <ScrollArea className="flex-1 px-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 text-sky-600">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No hay conversaciones aún</p>
              <p className="text-xs opacity-70">Crea una nueva para empezar</p>
            </div>
          ) : (
            <div className="space-y-2 pb-6">
              {conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={cn(
                    "group relative p-3 rounded-lg cursor-pointer transition-all",
                    "backdrop-blur-sm bg-white/40 border border-white/20 hover:bg-white/60",
                    activeConversationId === conversation.id && "bg-sky-100/60 border-sky-200/50"
                  )}
                  onClick={() => {
                    onSelectConversation(conversation);
                    if (!isLargeScreen) {
                      setOpen(false);
                    }
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-sky-700 truncate">
                        {conversation.title || 'Sin título'}
                      </h4>
                      <p className="text-xs text-sky-500 mt-1">
                        {formatDate(conversation.updated_at)}
                      </p>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-sky-600 hover:text-red-600 hover:bg-red-50"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conversation.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </>
  );
}