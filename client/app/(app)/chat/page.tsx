"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { AstroWebSocket } from "@/lib/websocket";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import ToolActivityIndicator from "@/components/chat/ToolActivityIndicator";
import SensitiveReadingDialog from "@/components/chat/SensitiveReadingDialog";

export default function ChatPage() {
  const {
    user,
    language,
    currentMessages,
    addMessage,
    isStreaming,
    setStreaming,
    streamingContent,
    setStreamingContent,
    appendStreamingContent,
    activeTool,
    setActiveTool,
  } = useAppStore();

  const [ws, setWs] = useState<AstroWebSocket | null>(null);
  const [confirmationPreview, setConfirmationPreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [currentMessages, streamingContent, scrollToBottom]);

  // Connect WebSocket
  useEffect(() => {
    if (!user) return;

    const sessionId = `session-${user.id}-${Date.now()}`;
    const socket = new AstroWebSocket(sessionId);

    socket.on("tool_start", (msg) => {
      setActiveTool({
        name: msg.tool_name || "",
        display: msg.display || "Processing...",
      });
    });

    socket.on("tool_end", () => {
      setActiveTool(null);
    });

    socket.on("token", (msg) => {
      if (!isStreaming) {
        setStreaming(true);
        setActiveTool(null);
      }
      appendStreamingContent(msg.content || "");
    });

    socket.on("done", () => {
      // Finalize the streamed message
      const finalContent = useAppStore.getState().streamingContent;
      if (finalContent) {
        addMessage({
          id: `msg-${Date.now()}`,
          conversation_id: "",
          role: "assistant",
          content: finalContent,
          language,
          created_at: new Date().toISOString(),
        });
      }
      setStreaming(false);
      setStreamingContent("");
    });

    socket.on("confirmation_required", (msg) => {
      setConfirmationPreview(msg.preview || "");
    });

    socket.on("error", (msg) => {
      console.error("WebSocket error:", msg.message);
      setStreaming(false);
      setStreamingContent("");
      setActiveTool(null);
    });

    socket.connect();
    setWs(socket);

    return () => {
      socket.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleSend = (content: string) => {
    if (!ws || !content.trim()) return;

    // Add user message immediately
    addMessage({
      id: `msg-${Date.now()}`,
      conversation_id: "",
      role: "user",
      content,
      language,
      created_at: new Date().toISOString(),
    });

    // Send via WebSocket
    ws.sendMessage(content, language);
  };

  const handleConfirmation = (confirmed: boolean) => {
    ws?.sendConfirmation(confirmed);
    setConfirmationPreview(null);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] md:h-screen">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
        {currentMessages.length === 0 && !isStreaming && !activeTool && (
          <div className="flex-1 flex items-center justify-center min-h-[60vh]">
            <div className="text-center max-w-md">
              <div className="w-4 h-4 rounded-full bg-solar-gold animate-pulse mx-auto mb-6" />
              <h2 className="font-headline-md text-2xl text-primary mb-3">
                Namaste, {user?.name}
              </h2>
              <p className="font-annotation-sm text-lg text-solar-gold mb-4">
                The cosmos awaits your question
              </p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Ask me about your birth chart, Dasha periods, today&apos;s
                Panchang, compatibility, auspicious timings, or any Vedic
                astrology question.
              </p>
            </div>
          </div>
        )}

        {currentMessages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Tool activity indicator */}
        {activeTool && (
          <ToolActivityIndicator
            toolName={activeTool.name}
            display={activeTool.display}
          />
        )}

        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <ChatMessage
            message={{
              id: "streaming",
              conversation_id: "",
              role: "assistant",
              content: streamingContent,
              created_at: new Date().toISOString(),
            }}
            isStreaming
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <ChatInput onSend={handleSend} disabled={isStreaming} />

      {/* Sensitive reading dialog */}
      <SensitiveReadingDialog
        open={!!confirmationPreview}
        preview={confirmationPreview || ""}
        onConfirm={() => handleConfirmation(true)}
        onDecline={() => handleConfirmation(false)}
      />
    </div>
  );
}
