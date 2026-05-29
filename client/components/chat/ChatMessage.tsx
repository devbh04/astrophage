import type { Message } from "@/lib/api";

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export default function ChatMessage({
  message,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
    >
      <div
        className={`max-w-[80%] md:max-w-[65%] ${
          isUser
            ? "bg-surface-container wobbly-border-sm px-5 py-3"
            : "glass-panel wobbly-border-sm px-5 py-4"
        }`}
      >
        {/* Role indicator */}
        <div className="flex items-center gap-2 mb-2">
          {isUser ? (
            <span className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              YOU
            </span>
          ) : (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-solar-gold" />
              <span className="font-nav-label text-[10px] uppercase tracking-widest text-solar-gold">
                ASTROPHAGE
              </span>
            </div>
          )}
        </div>

        {/* Message content */}
        <div
          className={`font-body-md text-body-md leading-relaxed ${
            isUser ? "text-on-surface" : "text-on-surface"
          }`}
        >
          {message.content}
          {isStreaming && (
            <span className="inline-block w-[2px] h-4 bg-solar-gold animate-pulse ml-[1px] align-text-bottom" />
          )}
        </div>
      </div>
    </div>
  );
}
