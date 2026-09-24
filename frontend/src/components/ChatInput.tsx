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
      <div className="relative flex w-full items-end rounded-3xl border border-rule bg-surface p-1 transition-colors focus-within:border-ledger focus-within:ring-2 focus-within:ring-ledger/15">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your data..."
          className="scrollbar-hide min-h-[48px] max-h-[150px] w-full flex-1 resize-none bg-transparent px-4 py-3 text-sm leading-relaxed text-ink placeholder-graphite focus:outline-none md:text-base"
          disabled={disabled}
          rows={1}
        />
        <div className="flex flex-shrink-0 pb-2 pl-2 pr-2">
          <button
            type="submit"
            disabled={!input.trim() || disabled}
            className={`
              flex items-center justify-center rounded-full p-2.5 transition-colors duration-300
              ${!input.trim() || disabled
                ? "cursor-not-allowed bg-paper-2 text-graphite"
                : "bg-ink text-paper hover:bg-ledger"}
            `}
          >
            <Send size={18} className="translate-x-[1px]" />
          </button>
        </div>
      </div>
      <div className="absolute -bottom-6 right-2 flex items-center space-x-1 text-[10px] text-graphite">
        <span>Press</span>
        <kbd className="flex items-center rounded-md border border-rule bg-paper-2 px-1.5 py-0.5">
          Enter <CornerDownLeft size={10} className="ml-1" />
        </kbd>
        <span>to send</span>
      </div>
    </form>
  );
}
