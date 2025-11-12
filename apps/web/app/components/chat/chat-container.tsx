import { useState, useEffect, useRef } from "react";
import { ChatMessageList } from "./chat-message-list";
import { ChatInput } from "./chat-input";

export interface Message {
  id: number;
  content: string;
  sender: 'user' | 'assistant';
}

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (messageContent: string) => {
    if (!messageContent.trim()) return;
    
    const newMessage: Message = {
      id: Date.now(),
      content: messageContent,
      sender: 'user'
    };
    
    setMessages(prev => [...prev, newMessage]);
    setInput('');
    
    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: Date.now() + 1,
        content: `Hola! Recibí tu mensaje: "${messageContent}"`,
        sender: 'assistant'
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen">
      <ChatMessageList 
        messages={messages} 
        messagesEndRef={messagesEndRef} 
      />
      <ChatInput 
        value={input}
        onChange={setInput}
        onSend={handleSendMessage}
      />
    </div>
  );
}