/**
 * HTTP chat API + lightweight tool-events WebSocket.
 *
 * The chat reply is fetched over plain HTTP — reliable, simple, no
 * streaming-state machine. A separate WebSocket at /ws/events streams only
 * ``tool_start`` and ``tool_end`` so the UI can show progress while the
 * fetch is in flight.
 */

import { api } from "./api";

export interface ChatCard {
  card_type: string;
  data: Record<string, unknown>;
}

export interface ChatReply {
  conversation_id: string;
  content: string;
  cards: ChatCard[];
  chart_svg: string | null;
  sensitive?: boolean;
  confirmation_preview?: string | null;
  error?: string | null;
}

export const chatApi = {
  send: (payload: {
    content: string;
    conversation_id?: string;
    language?: string;
  }) =>
    api<ChatReply>("/api/chat", {
      method: "POST",
      body: payload,
    }),

  confirm: (conversation_id: string, confirmed: boolean) =>
    api<ChatReply>(`/api/chat/${conversation_id}/confirm`, {
      method: "POST",
      body: { confirmed },
    }),
};

// ── Tool events WebSocket ──────────────────────────────────────

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:7860";

function readSessionCookie(): string | null {
  if (typeof document === "undefined") return null;
  for (const raw of document.cookie.split(";")) {
    const t = raw.trim();
    if (t.startsWith("astrophage_session=")) {
      return decodeURIComponent(t.slice("astrophage_session=".length));
    }
  }
  return null;
}

export type ToolEvent =
  | { type: "tool_start"; tool_name: string }
  | { type: "tool_end"; tool_name: string }
  | { type: "pong" };

export function connectEventsSocket(
  onEvent: (e: ToolEvent) => void
): () => void {
  let closed = false;
  let ws: WebSocket | null = null;
  let pingTimer: ReturnType<typeof setInterval> | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempts = 0;

  function open() {
    if (closed) return;
    const token = readSessionCookie();
    let url = `${WS_BASE}/ws/events`;
    if (token) url += `?token=${encodeURIComponent(token)}`;

    ws = new WebSocket(url);

    ws.onopen = () => {
      attempts = 0;
      pingTimer = setInterval(() => {
        try {
          ws?.send(JSON.stringify({ type: "ping" }));
        } catch {
          // ignore
        }
      }, 30000);
    };

    ws.onmessage = (evt) => {
      try {
        onEvent(JSON.parse(evt.data));
      } catch {
        // ignore malformed
      }
    };

    ws.onclose = () => {
      if (pingTimer) {
        clearInterval(pingTimer);
        pingTimer = null;
      }
      if (closed) return;
      const delay = Math.min(15000, 500 * Math.pow(2, attempts));
      attempts += 1;
      reconnectTimer = setTimeout(open, delay);
    };

    ws.onerror = () => {
      // Let onclose handle reconnects; nothing useful in the error event.
    };
  }

  open();

  return () => {
    closed = true;
    if (pingTimer) clearInterval(pingTimer);
    if (reconnectTimer) clearTimeout(reconnectTimer);
    try {
      ws?.close();
    } catch {
      /* ignore */
    }
  };
}
