import { cn } from "~/lib/utils";
import { type UIMessage } from "~/lib/api-client";
import { formatAssistantMessage, formatUserMessage } from "~/lib/markdown";

interface ChatMessageProps {
  message: UIMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.sender === 'user';

  return (
    <div className={cn(
      "flex",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div
        className={cn(
          "px-5 py-4 rounded-2xl shadow-lg",
          isUser
            ? "max-w-xs lg:max-w-md bg-sky-600 text-white"
            : "max-w-lg lg:max-w-2xl backdrop-blur-md bg-white/80 border border-white/50 text-sky-700"
        )}
      >
        {isUser 
          ? formatUserMessage(message.content)
          : formatAssistantMessage(message.content)
        }
      </div>
    </div>
  );
}