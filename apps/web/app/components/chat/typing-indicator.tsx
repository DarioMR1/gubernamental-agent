import { cn } from "~/lib/utils";

interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className }: TypingIndicatorProps) {
  return (
    <div className={cn("flex justify-start", className)}>
      <div className="max-w-xs lg:max-w-md px-4 py-3 rounded-2xl backdrop-blur-md bg-white/60 border border-white/50 text-sky-700">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce [animation-delay:-0.3s] animate-duration-[1.4s]"></div>
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce [animation-delay:-0.15s] animate-duration-[1.4s]"></div>
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce animate-duration-[1.4s]"></div>
          </div>
          <span className="text-sm text-sky-600 opacity-70">Escribiendo...</span>
        </div>
      </div>
    </div>
  );
}