/**
 * WebSocket client manager for real-time chat.
 *
 * Connects to /ws/{conversation_id} (or "new" for a fresh conversation),
 * dispatches typed events to subscribers, and resends a heartbeat.
 *
 * Auth: cookies don't reliably ride cross-origin WS handshakes (SameSite=lax
 * blocks them), so we read the session cookie client-side and forward the
 * JWT as a `?token=...` query param. The backend accepts either source.
 */

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:7860";

export type WsMessageType =
  | "tool_start"
  | "tool_end"
  | "token"
  | "confirmation_required"
  | "chart_svg"
  | "structured_card"
  | "conversation"
  | "done"
  | "error"
  | "pong";

export interface WsMessage {
  type: WsMessageType;
  tool_name?: string;
  display?: string;
  content?: string;
  preview?: string;
  svg?: string;
  card_type?: string;
  data?: Record<string, unknown>;
  conversation_id?: string;
  message?: string;
}

type MessageHandler = (msg: WsMessage) => void;

function readSessionCookie(): string | null {
  if (typeof document === "undefined") return null;
  for (const raw of document.cookie.split(";")) {
    const trimmed = raw.trim();
    if (trimmed.startsWith("astrophage_session=")) {
      return decodeURIComponent(trimmed.slice("astrophage_session=".length));
    }
  }
  return null;
}

export class AstroWebSocket {
  private ws: WebSocket | null = null;
  private conversationId: string;
  private handlers: Map<WsMessageType | "any", MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private _isConnected = false;
  private _shouldReconnect = true;

  constructor(conversationId: string) {
    this.conversationId = conversationId;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this._shouldReconnect = true;

    const token = readSessionCookie();
    let url = `${WS_BASE}/ws/${this.conversationId}`;
    if (token) {
      url += `?token=${encodeURIComponent(token)}`;
    }

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this._isConnected = true;
      this.reconnectAttempts = 0;
      this.pingInterval = setInterval(() => {
        this.send({ type: "ping" });
      }, 30000);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type === "conversation" && msg.conversation_id) {
          this.conversationId = msg.conversation_id;
        }
        this.dispatch(msg);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    this.ws.onclose = (event) => {
      this._isConnected = false;
      this.clearPing();
      const why = describeCloseCode(event.code);
      if (event.code === 4001) {
        console.warn(
          `[ws] auth failed (4001). Cookie present: ${!!token}. ` +
            `Make sure you're signed in and the backend is running at ${WS_BASE}.`
        );
        // Auth failures aren't going to recover by reconnecting.
        this._shouldReconnect = false;
      } else {
        console.warn(
          `[ws] closed (code=${event.code} ${why}). reason="${event.reason || ""}"`
        );
      }
      if (this._shouldReconnect) this.attemptReconnect();
    };

    this.ws.onerror = () => {
      // The browser doesn't expose useful details on WS errors. The
      // close handler above gets the actual code (4001 = auth failed,
      // 1006 = network/CORS/no server). Log a hint here.
      console.warn(
        `[ws] error connecting to ${url.split("?")[0]}. ` +
          `Backend reachable? ${WS_BASE}`
      );
    };
  }

  disconnect(): void {
    this._shouldReconnect = false;
    this.clearPing();
    this.ws?.close();
    this.ws = null;
    this._isConnected = false;
  }

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  sendMessage(content: string, language: string = "en"): void {
    this.send({ type: "message", content, language });
  }

  sendConfirmation(confirmed: boolean): void {
    this.send({ type: "confirmation", confirmed });
  }

  on(type: WsMessageType | "any", handler: MessageHandler): () => void {
    const existing = this.handlers.get(type) || [];
    existing.push(handler);
    this.handlers.set(type, existing);
    return () => {
      const handlers = this.handlers.get(type) || [];
      this.handlers.set(
        type,
        handlers.filter((h) => h !== handler)
      );
    };
  }

  private dispatch(msg: WsMessage): void {
    const typeHandlers = this.handlers.get(msg.type) || [];
    typeHandlers.forEach((h) => h(msg));
    const anyHandlers = this.handlers.get("any") || [];
    anyHandlers.forEach((h) => h(msg));
  }

  private clearPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(), delay);
  }
}

function describeCloseCode(code: number): string {
  switch (code) {
    case 1000:
      return "normal";
    case 1001:
      return "going-away";
    case 1006:
      return "abnormal — server unreachable or CORS";
    case 1011:
      return "server error";
    case 4001:
      return "auth failed";
    default:
      return "unknown";
  }
}
