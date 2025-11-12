export { ChatLayout } from "./chat-layout";
export { ChatContainer } from "./chat-container";
export { ChatMessage } from "./chat-message";
export { ChatMessageList } from "./chat-message-list";
export { ChatInput } from "./chat-input";
export { TypingIndicator } from "./typing-indicator";
export { ConversationsSidebar } from "./conversations-sidebar";

// Export types from api-client
export type { 
  UIMessage, 
  Message, 
  Conversation, 
  ConversationDetail,
  ChatRequest,
  ChatResponse 
} from "~/lib/api-client";