"""
Tiny in-process pub/sub for live tool-activity events.

The chat HTTP handler runs the agent and publishes ``tool_start`` /
``tool_end`` events to a per-user channel. A separate WebSocket
endpoint (``/ws/events``) subscribes to that user's channel and forwards
the events to the browser, so the UI can show a live "Running compute_dasha…"
indicator while the HTTP request is in flight.

This keeps the actual reply on a reliable HTTP request/response cycle
and reserves WebSockets only for ephemeral progress notifications.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    """Per-key fan-out queue."""

    def __init__(self) -> None:
        self._channels: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, key: str) -> asyncio.Queue:
        async with self._lock:
            q: asyncio.Queue = asyncio.Queue(maxsize=128)
            self._channels[key].append(q)
            return q

    async def unsubscribe(self, key: str, q: asyncio.Queue) -> None:
        async with self._lock:
            queues = self._channels.get(key, [])
            if q in queues:
                queues.remove(q)
            if not queues and key in self._channels:
                del self._channels[key]

    def publish(self, key: str, event: dict[str, Any]) -> None:
        for q in list(self._channels.get(key, [])):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop on overflow rather than backpressuring the agent.
                pass


# Singleton — module-level for the lifetime of the FastAPI process.
bus = EventBus()


__all__ = ["EventBus", "bus"]
