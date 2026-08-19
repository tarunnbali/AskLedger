import { useState, FormEvent, useRef, useEffect } from "react";
import { Send, CornerDownLeft } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input);
      setInput("");
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  return (
    <form onSubmit={handleSubmit} className="relative w-full flex flex-col pt-2">
      <div className="relative flex items-end w-full glass rounded-3xl p-1 shadow-lg border border-[#3b82f6]/30 bg-[#121212]/80 focus-within:ring-2 focus-within:ring-[#3b82f6]/50 transition-all duration-300">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          className="w-full bg-transparent text-gray-100 placeholder-gray-500 px-4 py-3 max-h-[150px] min-h-[48px] resize-none focus:outline-none scrollbar-hide text-sm md:text-base leading-relaxed flex-1"
          disabled={disabled}
          rows={1}
        />
        <div className="flex-shrink-0 flex pr-2 pb-2 pl-2">
          <button
            type="submit"
            disabled={!input.trim() || disabled}
            className={`
              p-2.5 rounded-full flex items-center justify-center transition-all duration-300
              ${!input.trim() || disabled 
                ? "bg-white/5 text-gray-500 cursor-not-allowed" 
                : "bg-blue-600 text-white shadow-[0_0_15px_rgba(59,130,246,0.5)] hover:bg-blue-500 hover:scale-105 active:scale-95"}
            `}
          >
            <Send size={18} className="translate-x-[1px]" />
          </button>
        </div>
      </div>
      <div className="absolute -bottom-6 right-2 flex items-center text-[10px] text-gray-500 space-x-1 opacity-60">
        <span>Press</span>
        <kbd className="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 flex items-center">
          Enter <CornerDownLeft size={10} className="ml-1" />
        </kbd>
        <span>to send</span>
      </div>
    </form>
  );
}
