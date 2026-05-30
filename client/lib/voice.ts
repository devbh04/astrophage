/**
 * Voice mode wire protocol — see backend/app/api/voice.py.
 *
 * Browser → server: 16 kHz mono PCM16 binary frames + JSON {type:"start"|"stop"}.
 * Server → browser: 24 kHz mono PCM16 binary frames + JSON control frames.
 */

export type VoiceEvent =
  | { type: "ready" }
  | { type: "tool_start"; tool_name: string }
  | { type: "tool_end"; tool_name: string; ok?: boolean }
  | { type: "structured_card"; card_type: string; data: Record<string, unknown> }
  | { type: "chart_svg"; svg: string }
  | { type: "input_transcription"; text: string }
  | { type: "output_transcription"; text: string }
  | { type: "turn_complete" }
  | { type: "error"; message: string };

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

export interface VoiceSocketHandlers {
  onAudio: (chunk: ArrayBuffer) => void;
  onEvent: (e: VoiceEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface VoiceSocket {
  sendAudio: (pcm16: ArrayBuffer) => void;
  stop: () => void;
  isOpen: () => boolean;
}

export function connectVoiceSocket(handlers: VoiceSocketHandlers): VoiceSocket {
  let ws: WebSocket | null = null;
  let closed = false;

  const token = readSessionCookie();
  let url = `${WS_BASE}/ws/voice`;
  if (token) url += `?token=${encodeURIComponent(token)}`;

  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    try {
      ws?.send(JSON.stringify({ type: "start" }));
    } catch {
      // ignore
    }
    handlers.onOpen?.();
  };

  ws.onmessage = (evt) => {
    if (typeof evt.data === "string") {
      try {
        const parsed = JSON.parse(evt.data) as VoiceEvent;
        handlers.onEvent(parsed);
      } catch {
        // ignore malformed
      }
      return;
    }
    if (evt.data instanceof ArrayBuffer) {
      handlers.onAudio(evt.data);
      return;
    }
    if (evt.data instanceof Blob) {
      evt.data.arrayBuffer().then(handlers.onAudio).catch(() => {});
    }
  };

  ws.onclose = () => {
    closed = true;
    handlers.onClose?.();
  };

  ws.onerror = () => {
    // onclose handles cleanup
  };

  return {
    sendAudio: (pcm16: ArrayBuffer) => {
      if (closed || !ws || ws.readyState !== WebSocket.OPEN) return;
      try {
        ws.send(pcm16);
      } catch {
        // ignore
      }
    },
    stop: () => {
      closed = true;
      try {
        ws?.send(JSON.stringify({ type: "stop" }));
      } catch {
        // ignore
      }
      try {
        ws?.close();
      } catch {
        // ignore
      }
      ws = null;
    },
    isOpen: () => !!ws && ws.readyState === WebSocket.OPEN,
  };
}
