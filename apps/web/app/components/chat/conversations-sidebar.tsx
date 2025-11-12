import { useState } from "react";
import { Plus, MessageSquare, Trash2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "~/components/ui/sheet";
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
}

export function ConversationsSidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isLoading = false,
}: ConversationsSidebarProps) {
  const [open, setOpen] = useState(false);

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
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="fixed top-4 left-4 z-50 backdrop-blur-md bg-white/60 border border-white/30 text-sky-700 hover:bg-white/70 hover:text-sky-800 transition-all"
        >
          <MessageSquare className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      
      <SheetContent 
        side="left" 
        className="w-80 p-0 backdrop-blur-md bg-white/90 border-r border-white/30"
      >
        <SheetHeader className="p-6 pb-4">
          <SheetTitle className="text-sky-700 font-semibold text-lg">
            Conversaciones
          </SheetTitle>
        </SheetHeader>
        
        <div className="px-6 pb-4">
          <Button
            onClick={() => {
              onNewConversation();
              setOpen(false);
            }}
            className="w-full bg-sky-600 hover:bg-sky-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Nueva conversación
          </Button>
        </div>

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
                    setOpen(false);
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
      </SheetContent>
    </Sheet>
  );
}