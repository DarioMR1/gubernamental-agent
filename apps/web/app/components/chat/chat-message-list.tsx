import { ScrollArea } from "~/components/ui/scroll-area";
import { ChatMessage } from "./chat-message";
import { TypingIndicator } from "./typing-indicator";
import { type Message } from "./chat-container";

interface ChatMessageListProps {
  messages: Message[];
  isTyping: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

export function ChatMessageList({ messages, isTyping, messagesEndRef }: ChatMessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
      <div className="max-w-3xl mx-auto space-y-4">
        {messages.length === 0 ? (
          <div className="text-center pt-16">
            <h1 className="text-4xl font-bold text-sky-700 dark:text-sky-600 mb-4">
              Chat Assistant
            </h1>
            <p className="text-sky-600 dark:text-sky-500">
              ¿En qué puedo ayudarte hoy?
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))
        )}
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}