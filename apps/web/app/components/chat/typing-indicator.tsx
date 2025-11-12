export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="max-w-xs lg:max-w-md px-6 py-4 rounded-2xl bg-white/80 backdrop-blur-sm border border-white/30 shadow-sm">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
          <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
          <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce"></div>
        </div>
      </div>
    </div>
  );
}