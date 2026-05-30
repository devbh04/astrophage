import MarkdownProse from "./MarkdownProse";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export default function ChatMessage({
  role,
  content,
  isStreaming = false,
}: ChatMessageProps) {
  const isUser = role === "user";
  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } animate-in fade-in slide-in-from-bottom-2 duration-300`}
    >
      <div
        className={`max-w-[85%] md:max-w-[75%] ${
          isUser
            ? "bg-surface-container wobbly-border-sm px-5 py-3"
            : "glass-panel wobbly-border-sm px-5 py-4"
        }`}
      >
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
        {isUser ? (
          <div className="font-body-md text-body-md leading-relaxed text-on-surface whitespace-pre-wrap">
            {content}
            {isStreaming && (
              <span className="inline-block w-px h-4 bg-solar-gold animate-pulse ml-px align-text-bottom" />
            )}
          </div>
        ) : (
          <div className="relative">
            <MarkdownProse content={content} />
            {isStreaming && (
              <span className="inline-block w-px h-4 bg-solar-gold animate-pulse ml-px align-text-bottom" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
