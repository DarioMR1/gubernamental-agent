import { cn } from "~/lib/utils";
import { type UIMessage } from "~/lib/api-client";

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
          "max-w-xs lg:max-w-md px-4 py-2 rounded-2xl",
          isUser
            ? "bg-sky-600 text-white"
            : "backdrop-blur-md bg-white/60 border border-white/50 text-sky-700"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}