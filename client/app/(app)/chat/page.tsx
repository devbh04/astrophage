"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore, createArtifactId } from "@/lib/store";
import { AstroWebSocket } from "@/lib/websocket";
import { conversationsApi } from "@/lib/api";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import ToolActivityIndicator from "@/components/chat/ToolActivityIndicator";
import SensitiveReadingDialog from "@/components/chat/SensitiveReadingDialog";
import StructuredCard from "@/components/cards/StructuredCard";
import ChartSvgCard from "@/components/cards/ChartSvgCard";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationParam = searchParams.get("c");

  const {
    user,
    language,
    artifacts,
    pushArtifact,
    appendStreamingText,
    finalizeStreamingText,
    clearArtifacts,
    hydrateFromMessages,
    isStreaming,
    setStreaming,
    activeTool,
    setActiveTool,
    activeConversationId,
    setActiveConversationId,
  } = useAppStore();

  const [ws, setWs] = useState<AstroWebSocket | null>(null);
  const [confirmationPreview, setConfirmationPreview] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingMsgIdRef = useRef<string | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [artifacts, activeTool, scrollToBottom]);

  // Load existing messages when resuming a conversation
  useEffect(() => {
    if (!conversationParam) return;
    setActiveConversationId(conversationParam);
    conversationsApi
      .messages(conversationParam)
      .then((msgs) => hydrateFromMessages(msgs))
      .catch(() => {});
  }, [conversationParam, hydrateFromMessages, setActiveConversationId]);

  // Connect WebSocket
  useEffect(() => {
    if (!user) return;

    const wsKey = conversationParam || "new";
    const socket = new AstroWebSocket(wsKey);

    socket.on("conversation", (msg) => {
      if (msg.conversation_id && msg.conversation_id !== "") {
        setActiveConversationId(msg.conversation_id);
        // Only update the URL once we have a real conversation
        if (!conversationParam) {
          router.replace(`/chat?c=${msg.conversation_id}`);
        }
      }
    });

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
      if (!streamingMsgIdRef.current) {
        const id = createArtifactId();
        streamingMsgIdRef.current = id;
        pushArtifact({
          kind: "text",
          id,
          role: "assistant",
          content: "",
          streaming: true,
          created_at: new Date().toISOString(),
        });
        setStreaming(true);
        setActiveTool(null);
      }
      appendStreamingText(streamingMsgIdRef.current!, msg.content || "");
    });

    socket.on("structured_card", (msg) => {
      pushArtifact({
        kind: "card",
        id: createArtifactId(),
        card_type: msg.card_type || "info",
        data: msg.data || {},
        created_at: new Date().toISOString(),
      });
    });

    socket.on("chart_svg", (msg) => {
      if (msg.svg) {
        pushArtifact({
          kind: "chart_svg",
          id: createArtifactId(),
          svg: msg.svg,
          created_at: new Date().toISOString(),
        });
      }
    });

    socket.on("done", () => {
      const id = streamingMsgIdRef.current;
      if (id) finalizeStreamingText(id);
      streamingMsgIdRef.current = null;
      setStreaming(false);
    });

    socket.on("confirmation_required", (msg) => {
      setConfirmationPreview(msg.preview || "");
    });

    socket.on("error", (msg) => {
      console.error("WebSocket error:", msg.message);
      setStreaming(false);
      setActiveTool(null);
      const id = streamingMsgIdRef.current;
      if (id) finalizeStreamingText(id);
      streamingMsgIdRef.current = null;
    });

    socket.connect();
    setWs(socket);

    return () => {
      socket.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, conversationParam]);

  const handleNewChat = () => {
    clearArtifacts();
    streamingMsgIdRef.current = null;
    setActiveConversationId(null);
    router.replace("/chat");
  };

  const handleSend = (content: string) => {
    if (!ws || !content.trim()) return;
    pushArtifact({
      kind: "text",
      id: createArtifactId(),
      role: "user",
      content,
      created_at: new Date().toISOString(),
    });
    ws.sendMessage(content, language);
  };

  const handleConfirmation = (confirmed: boolean) => {
    ws?.sendConfirmation(confirmed);
    setConfirmationPreview(null);
  };

  const empty = artifacts.length === 0 && !isStreaming && !activeTool;

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] md:h-screen">
      <div className="flex items-center justify-between px-4 md:px-8 py-3 border-b border-dashed border-outline/20">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-solar-gold animate-pulse" />
          <span className="font-nav-label text-xs uppercase tracking-widest text-on-surface-variant">
            {activeConversationId ? "Live conversation" : "New conversation"}
          </span>
        </div>
        <button
          onClick={handleNewChat}
          className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-solar-gold transition-colors"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-4">
        {empty && (
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
                Ask about your birth chart, dasha periods, today&apos;s
                Panchang, compatibility, auspicious timings, or any Vedic
                astrology question.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6">
                {[
                  "Show my full birth chart",
                  "What's my current Mahadasha?",
                  "Today's Panchang in Mumbai",
                  "Am I in Sade Sati?",
                ].map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="text-left text-xs font-body-md text-on-surface-variant hover:text-solar-gold px-3 py-2 wobbly-border-sm bg-surface-container-low/60 hover:bg-surface-container/80 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {artifacts.map((a) => {
          if (a.kind === "text") {
            return (
              <ChatMessage
                key={a.id}
                role={a.role}
                content={a.content}
                isStreaming={!!a.streaming}
              />
            );
          }
          if (a.kind === "card") {
            return (
              <div
                key={a.id}
                className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300"
              >
                <StructuredCard cardType={a.card_type} data={a.data} />
              </div>
            );
          }
          if (a.kind === "chart_svg") {
            return (
              <div
                key={a.id}
                className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300"
              >
                <ChartSvgCard svg={a.svg} />
              </div>
            );
          }
          return null;
        })}

        {activeTool && (
          <ToolActivityIndicator
            toolName={activeTool.name}
            display={activeTool.display}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={isStreaming} />

      <SensitiveReadingDialog
        open={!!confirmationPreview}
        preview={confirmationPreview || ""}
        onConfirm={() => handleConfirmation(true)}
        onDecline={() => handleConfirmation(false)}
      />
    </div>
  );
}
