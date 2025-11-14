import { ScrollArea } from "~/components/ui/scroll-area";
import { ChatMessage } from "./chat-message";
import { TypingIndicator } from "./typing-indicator";
import { type UIMessage } from "~/lib/api-client";

interface ChatMessageListProps {
  messages: UIMessage[];
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  welcomeTitle?: string;
  welcomeMessage?: string;
  isWaitingForFirstToken?: boolean;
  onSendMessage?: (message: string) => void;
}

export function ChatMessageList({ 
  messages, 
  messagesEndRef, 
  welcomeTitle = "Chat Assistant",
  welcomeMessage = "¿En qué puedo ayudarte hoy?",
  isWaitingForFirstToken = false,
  onSendMessage
}: ChatMessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
      <div className="max-w-3xl mx-auto space-y-4">
        {messages.length === 0 ? (
          <div className="text-center pt-16">
            <h1 className="text-4xl font-bold text-sky-700 dark:text-sky-600 mb-4">
              {welcomeTitle}
            </h1>
            <p className="text-sky-600 dark:text-sky-500">
              {welcomeMessage}
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message} 
              onSendMessage={onSendMessage}
            />
          ))
        )}
        {isWaitingForFirstToken && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}