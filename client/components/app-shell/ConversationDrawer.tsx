"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Trash2, MessageCircle, Plus } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { conversationsApi, type Conversation } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const fmt = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
};

export default function ConversationDrawer({ open, onOpenChange }: Props) {
  const router = useRouter();
  const params = useSearchParams();
  const pathname = usePathname();
  const activeId = params.get("c");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    conversationsApi
      .list()
      .then((c) => setConversations(c))
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, [open]);

  const handleOpen = (id: string) => {
    onOpenChange(false);
    if (pathname === "/chat") {
      router.replace(`/chat?c=${id}`);
    } else {
      router.push(`/chat?c=${id}`);
    }
  };

  const handleNew = () => {
    onOpenChange(false);
    router.push("/chat");
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this conversation?")) return;
    try {
      await conversationsApi.delete(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) router.push("/chat");
    } catch {
      // ignore
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="left"
        className="bg-surface-container-lowest border-r border-dashed border-outline/20 w-80 px-4"
      >
        <SheetHeader>
          <SheetTitle className="font-headline-md text-lg text-primary">
            Conversations
          </SheetTitle>
        </SheetHeader>

        <div className="mt-4 px-10">
          <button
            onClick={handleNew}
            className="w-full btn-primary wobbly-border-sm py-2 font-nav-label text-[10px] uppercase tracking-widest flex items-center justify-center gap-2"
          >
            <Plus size={14} />
            New chat
          </button>
        </div>

        <div className="mt-4 space-y-1 overflow-y-auto max-h-[calc(100vh-160px)]">
          {loading ? (
            <p className="text-center font-body-md text-xs text-on-surface-variant py-4">
              Loading…
            </p>
          ) : conversations.length === 0 ? (
            <p className="text-center font-body-md text-xs text-on-surface-variant py-4">
              No past conversations.
            </p>
          ) : (
            conversations.map((c) => {
              const isActive = c.id === activeId;
              return (
                <div
                  key={c.id}
                  className={`group flex items-center gap-2 wobbly-border-sm px-3 py-2 transition-colors cursor-pointer ${
                    isActive
                      ? "bg-solar-gold/10 border-solar-gold/40"
                      : "hover:bg-surface-container/60 border-outline/20"
                  }`}
                  onClick={() => handleOpen(c.id)}
                >
                  <MessageCircle
                    size={14}
                    className={isActive ? "text-solar-gold" : "text-on-surface-variant"}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-headline-md text-sm text-primary truncate">
                      {c.title || "Chat"}
                    </div>
                    <div className="font-body-md text-[10px] text-on-surface-variant">
                      {fmt(c.created_at)}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(c.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 transition-opacity"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
