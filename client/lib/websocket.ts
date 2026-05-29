/**
 * WebSocket client manager for real-time chat.
 *
 * Handles connection, reconnection, message parsing,
 * and event dispatching.
 */

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:7860";

export type WsMessageType =
  | "tool_start"
  | "tool_end"
  | "token"
  | "confirmation_required"
  | "chart_svg"
  | "structured_card"
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
  message?: string;
}

type MessageHandler = (msg: WsMessage) => void;

export class AstroWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private handlers: Map<WsMessageType | "any", MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private _isConnected = false;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${WS_BASE}/ws/${this.sessionId}`);

    this.ws.onopen = () => {
      this._isConnected = true;
      this.reconnectAttempts = 0;

      // Start heartbeat
      this.pingInterval = setInterval(() => {
        this.send({ type: "ping" });
      }, 30000);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        this.dispatch(msg);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    this.ws.onclose = () => {
      this._isConnected = false;
      this.clearPing();
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  }

  disconnect(): void {
    this.maxReconnectAttempts = 0; // Prevent reconnection
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

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type) || [];
      this.handlers.set(
        type,
        handlers.filter((h) => h !== handler)
      );
    };
  }

  private dispatch(msg: WsMessage): void {
    // Dispatch to type-specific handlers
    const typeHandlers = this.handlers.get(msg.type) || [];
    typeHandlers.forEach((h) => h(msg));

    // Dispatch to "any" handlers
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

    setTimeout(() => {
      this.connect();
    }, delay);
  }
}
