"use client";

import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  }, [value]);

  const handleSubmit = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-dashed border-outline/20 px-4 md:px-8 py-4 bg-background/80 backdrop-blur-md">
      <div className="max-w-3xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your destiny..."
            disabled={disabled}
            rows={1}
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant resize-none min-h-[48px] max-h-[160px] pr-4 focus:border-solar-gold focus:ring-solar-gold/20"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!value.trim() || disabled}
          className="btn-primary wobbly-border-sm p-3 shrink-0 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Send size={18} />
        </button>
      </div>
      <p className="text-center mt-2 font-nav-label text-[9px] uppercase tracking-widest text-outline-variant">
        SHIFT + ENTER for new line • ENTER to send
      </p>
    </div>
  );
}
