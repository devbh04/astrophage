"""
AstroAgent Backend — FastAPI application.

Replies are served via plain HTTP `POST /api/chat`.

A thin WebSocket at `/ws/events` carries only ephemeral progress events
(``tool_start`` / ``tool_end``) so the frontend can render a "Running
compute_dasha…" indicator while the HTTP request is in flight.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.auth.routes import router as auth_router
from app.auth.service import decode_jwt
from app.api.profiles import router as profiles_router
from app.api.conversations import router as conversations_router
from app.api.panchang import router as panchang_router
from app.api.tools import router as tools_router
from app.api.chat import router as chat_router
from app.agent._event_bus import bus
from app.db.queries import get_user_by_id


# ── Logging ────────────────────────────────────────────────────
# uvicorn's default config doesn't show `app.*` INFO lines. Wire one up
# here so logger.info() calls inside the chat / agent modules print
# to the same console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Quiet down very chatty libraries
for noisy in ("httpx", "httpcore", "google_genai", "supabase", "hpack"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Astrophage API",
    description="AI Vedic Astrology Backend",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(conversations_router)
app.include_router(panchang_router)
app.include_router(tools_router)
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "astrophage"}


SECRET_RE = re.compile(r"(?:GOOGLE_API_KEY|QDRANT_API_KEY|JWT_SECRET)\s*[=:]\s*\S+")


def _redact(message: str) -> str:
    return SECRET_RE.sub("[redacted]", message)


async def _authenticate_or_close(websocket: WebSocket) -> dict | None:
    """Cookie first, then `?token=...` query param fallback."""
    token = websocket.cookies.get("astrophage_session")
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        try:
            await websocket.close(code=4001)
        except Exception:
            pass
        return None
    try:
        payload = decode_jwt(token)
        user = await get_user_by_id(payload["sub"])
    except Exception:
        user = None
    if not user:
        try:
            await websocket.close(code=4001)
        except Exception:
            pass
        return None
    return user


# ── Events WebSocket ───────────────────────────────────────────


@app.websocket("/ws/events")
async def events_socket(websocket: WebSocket):
    """
    Subscribe to live tool-activity events for the authenticated user.
    Frames forwarded as JSON: ``{type, tool_name}``.
    """
    await websocket.accept()
    user = await _authenticate_or_close(websocket)
    if not user:
        return

    queue = await bus.subscribe(user["id"])
    receive_task: asyncio.Task | None = None

    async def _drain_inbound():
        # The browser only sends pings; consume and discard until disconnect.
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                if data.get("type") == "ping":
                    try:
                        await websocket.send_json({"type": "pong"})
                    except Exception:
                        return
        except (WebSocketDisconnect, RuntimeError):
            return

    try:
        receive_task = asyncio.create_task(_drain_inbound())
        while True:
            event = await queue.get()
            try:
                await websocket.send_json(event)
            except Exception:
                break
            if receive_task.done():
                break
    except Exception as exc:
        logger.warning("events socket: %s", _redact(str(exc)))
    finally:
        await bus.unsubscribe(user["id"], queue)
        if receive_task and not receive_task.done():
            receive_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
