/**
 * StrictMode-safe singleton for the /ws/events tool-event channel.
 *
 * React 18+ in dev double-mounts every effect, which opens then immediately
 * tears down our WebSocket. The previous code created a new WS per mount
 * and the cleanup of mount #1 closed mount #2's socket too.
 *
 * This module keeps one WebSocket alive across all mounts on the page.
 * Subscribers register via ``subscribe()`` and get a cleanup fn. The socket
 * itself only opens on the first subscriber and closes when the last
 * subscriber leaves (with a small grace period to absorb the StrictMode
 * mount-unmount-remount cycle).
 */

import { connectEventsSocket, type ToolEvent } from "./chat";

type Listener = (e: ToolEvent) => void;

let close: (() => void) | null = null;
let listeners: Listener[] = [];
let pendingDisposeTimer: ReturnType<typeof setTimeout> | null = null;

function startSocket() {
  if (close) return;
  close = connectEventsSocket((event) => {
    for (const l of listeners) l(event);
  });
}

function stopSocket() {
  if (close) {
    try {
      close();
    } catch {
      /* ignore */
    }
    close = null;
  }
}

export function subscribeEvents(listener: Listener): () => void {
  // Cancel any pending teardown — a re-mount happened within the grace period.
  if (pendingDisposeTimer) {
    clearTimeout(pendingDisposeTimer);
    pendingDisposeTimer = null;
  }
  listeners.push(listener);
  startSocket();

  return () => {
    listeners = listeners.filter((l) => l !== listener);
    if (listeners.length === 0) {
      // Defer the actual close so a StrictMode remount can rescue us.
      pendingDisposeTimer = setTimeout(() => {
        if (listeners.length === 0) stopSocket();
        pendingDisposeTimer = null;
      }, 80);
    }
  };
}
