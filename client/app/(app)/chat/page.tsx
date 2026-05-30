"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAppStore, createArtifactId } from "@/lib/store";
import { conversationsApi } from "@/lib/api";
import { chatApi, type ChatToolRun } from "@/lib/chat";
import { subscribeEvents } from "@/lib/events_singleton";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import ToolActivityIndicator from "@/components/chat/ToolActivityIndicator";
import ToolBadgeStrip from "@/components/chat/ToolBadgeStrip";
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
    clearArtifacts,
    hydrateFromMessages,
    isStreaming,
    setStreaming,
    activeTool,
    setActiveTool,
    activeConversationId,
    setActiveConversationId,
  } = useAppStore();

  const [confirmationPreview, setConfirmationPreview] = useState<string | null>(null);
  const [convId, setConvId] = useState<string | null>(conversationParam);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [artifacts, activeTool, scrollToBottom]);

  useEffect(() => {
    setConvId(conversationParam);
  }, [conversationParam]);

  // Hydrate history when arriving on an existing conversation
  useEffect(() => {
    if (!conversationParam) {
      clearArtifacts();
      setActiveConversationId(null);
      return;
    }
    setActiveConversationId(conversationParam);
    conversationsApi
      .messages(conversationParam)
      .then((msgs) => hydrateFromMessages(msgs))
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationParam]);

  // Live tool-event channel — single shared WS across the whole page.
  useEffect(() => {
    if (!user) return;
    const unsubscribe = subscribeEvents((e) => {
      console.debug("[events] received:", e);
      if (e.type === "tool_start") {
        setActiveTool({
          name: e.tool_name,
          display: `Running ${e.tool_name.replace(/_/g, " ")}…`,
        });
      }
      // Intentionally do NOT clear on tool_end: the LLM may run another
      // reasoning pass before the next tool, and clearing here causes the
      // generic "Consulting the stars" indicator to flash back into view
      // for a split second between calls. Leave the last tool pinned —
      // either the next tool_start replaces it, or the HTTP request's
      // finally block clears it when the whole turn completes.
    });
    return unsubscribe;
  }, [user, setActiveTool]);

  const renderReply = useCallback(
    (reply: {
      content?: string;
      cards?: { card_type: string; data: Record<string, unknown> }[];
      chart_svg?: string | null;
      tool_runs?: ChatToolRun[];
    }) => {
      if (reply.chart_svg) {
        pushArtifact({
          kind: "chart_svg",
          id: createArtifactId(),
          svg: reply.chart_svg,
          created_at: new Date().toISOString(),
        });
      }
      for (const c of reply.cards || []) {
        pushArtifact({
          kind: "card",
          id: createArtifactId(),
          card_type: c.card_type,
          data: c.data || {},
          created_at: new Date().toISOString(),
        });
      }
      if (reply.content) {
        pushArtifact({
          kind: "text",
          id: createArtifactId(),
          role: "assistant",
          content: reply.content,
          toolRuns: reply.tool_runs && reply.tool_runs.length > 0
            ? reply.tool_runs
            : undefined,
          created_at: new Date().toISOString(),
        });
      }
    },
    [pushArtifact]
  );

  const showError = useCallback(
    (err: unknown) => {
      const msg = err instanceof Error ? err.message : String(err || "");
      let friendly = msg;
      if (/quota|RESOURCE_EXHAUSTED|429/i.test(msg)) {
        friendly =
          "I'm out of LLM quota for the moment — Google's free tier limits " +
          "Gemini calls per day. Please try again later, or upgrade billing.";
      } else if (!friendly) {
        friendly = "Something went wrong. Please try again.";
      }
      pushArtifact({
        kind: "text",
        id: createArtifactId(),
        role: "assistant",
        content: `⚠️ ${friendly}`,
        created_at: new Date().toISOString(),
      });
    },
    [pushArtifact]
  );

  const handleSend = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isStreaming) return;

      pushArtifact({
        kind: "text",
        id: createArtifactId(),
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      });
      setStreaming(true);
      setActiveTool(null);

      try {
        const reply = await chatApi.send({
          content: trimmed,
          conversation_id: convId || undefined,
          language,
        });

        console.debug("[chat] reply:", {
          conversation_id: reply.conversation_id,
          content_len: (reply.content || "").length,
          cards: (reply.cards || []).length,
          chart_svg: !!reply.chart_svg,
          tool_runs: reply.tool_runs?.map((r) => `${r.tool}(${r.status})`),
          sensitive: reply.sensitive,
          error: reply.error,
        });

        if (reply.error) {
          showError(reply.error);
          return;
        }

        // Pick up new conversation id and update URL silently
        if (reply.conversation_id && reply.conversation_id !== convId) {
          setConvId(reply.conversation_id);
          setActiveConversationId(reply.conversation_id);
          if (!conversationParam) {
            try {
              window.history.replaceState(
                window.history.state,
                "",
                `/chat?c=${reply.conversation_id}`
              );
            } catch {
              router.replace(`/chat?c=${reply.conversation_id}`);
            }
          }
        }

        if (reply.sensitive) {
          setConfirmationPreview(reply.confirmation_preview || "Continue?");
          renderReply(reply);
          return;
        }

        renderReply(reply);
      } catch (err) {
        showError(err);
      } finally {
        setStreaming(false);
        setActiveTool(null);
      }
    },
    [
      convId,
      conversationParam,
      isStreaming,
      language,
      pushArtifact,
      renderReply,
      router,
      setActiveConversationId,
      setActiveTool,
      setStreaming,
      showError,
    ]
  );

  const handleConfirmation = useCallback(
    async (confirmed: boolean) => {
      const id = convId;
      setConfirmationPreview(null);
      if (!id) return;
      setStreaming(true);
      try {
        const reply = await chatApi.confirm(id, confirmed);
        if (reply.error) {
          showError(reply.error);
          return;
        }
        renderReply(reply);
      } catch (err) {
        showError(err);
      } finally {
        setStreaming(false);
        setActiveTool(null);
      }
    },
    [convId, renderReply, setActiveTool, setStreaming, showError]
  );

  const handleNewChat = () => {
    clearArtifacts();
    setConvId(null);
    setActiveConversationId(null);
    router.replace("/chat");
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
              <div key={a.id} className="flex flex-col">
                <ChatMessage
                  role={a.role}
                  content={a.content}
                  isStreaming={!!a.streaming}
                />
                {a.role === "assistant" && a.toolRuns && a.toolRuns.length > 0 && (
                  <div className="flex justify-start mt-1 ml-1">
                    <ToolBadgeStrip runs={a.toolRuns} />
                  </div>
                )}
              </div>
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

        {isStreaming && !activeTool && (
          <ToolActivityIndicator
            toolName="reasoning"
            display="Thinking…"
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
