import { useState } from "react";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: (message: string) => void;
}

export function ChatInput({ value, onChange, onSend }: ChatInputProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSend(value);
    }
  };

  return (
    <div className="p-6 pb-8">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="flex gap-3">
          <Input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Escribe tu mensaje..."
            className="flex-1 px-6 py-4 h-12 rounded-full backdrop-blur-md bg-white/60 border border-white/30 text-sky-700 placeholder:text-sky-500 focus-visible:border-sky-300 focus-visible:bg-white/70 transition-all focus-visible:ring-sky-300/50"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!value.trim()}
            className="w-12 h-12 bg-sky-600 hover:bg-sky-700 text-white rounded-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ↑
          </Button>
        </div>
      </form>
    </div>
  );
}