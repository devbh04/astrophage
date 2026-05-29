"""
AstroAgent Backend — FastAPI application.

Phase 4 WebSocket handler:
- Authenticates from JWT cookie on accept (close 4001 on failure).
- Pre-loads natal chart + active dashas from `birth_profiles` (relationship = "self").
- Streams agent graph events via `astream_events(version="v2")`.
- Maps LangGraph events to wire frames per design §4.
- Honors HiTL interrupts (sensitive turns) with confirmation_required + resume.
"""

from __future__ import annotations

import json
import logging
import re
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from app.config import get_settings
from app.auth.routes import router as auth_router
from app.auth.service import decode_jwt
from app.api.profiles import router as profiles_router
from app.api.conversations import router as conversations_router
from app.api.panchang import router as panchang_router
from app.agent.graph import agent_graph
from app.db.queries import (
    get_user_by_id,
    create_conversation,
    create_message,
    get_self_profile,
)

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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "astrophage"}


# ── Helpers ─────────────────────────────────────────────────────


SECRET_RE = re.compile(r"(?:GOOGLE_API_KEY|QDRANT_API_KEY|JWT_SECRET)\s*=\s*\S+")


def _redact(message: str) -> str:
    return SECRET_RE.sub("[redacted]", message)


async def _authenticate_or_close(websocket: WebSocket) -> dict | None:
    """Decode the JWT cookie, return the user dict, or close with 4001."""
    cookies = websocket.cookies
    token = cookies.get("astrophage_session")
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


async def _load_self_profile(user_id: str) -> tuple[dict | None, dict | None, str | None]:
    """Return (natal_chart, computed_dashas, profile_id) for the user's self profile."""
    try:
        profile = await get_self_profile(user_id)
    except Exception:
        profile = None
    if not profile:
        return None, None, None
    return (
        profile.get("computed_chart"),
        profile.get("computed_dashas"),
        profile.get("id"),
    )


def _initial_state(
    user: dict,
    session_id: str,
    content: str,
    language: str | None,
    natal_chart: dict | None,
    active_dashas: dict | None,
) -> dict:
    return {
        "messages": [HumanMessage(content=content)],
        "user_id": user["id"],
        "session_id": session_id,
        "language": language or user.get("default_language") or "en",
        "natal_chart": natal_chart or {},
        "active_dashas": active_dashas or {},
        "intent": "",
        "tool_outputs": [],
        "sensitive_flag": False,
        "awaiting_confirmation": False,
        "confirmed": False,
    }


async def _stream_agent_turn(
    websocket: WebSocket,
    thread_id: str,
    initial_state: dict,
    conversation_id: str,
) -> None:
    """Run a graph turn and forward events as wire frames."""
    config = {"configurable": {"thread_id": thread_id}}
    final_text = ""
    streamed_any_token = False
    chart_svg = None
    structured_card = None
    interrupted = False

    try:
        async for event in agent_graph.astream_events(initial_state, config=config, version="v2"):
            etype = event.get("event")
            data = event.get("data") or {}
            name = event.get("name")

            if etype == "on_tool_start":
                await websocket.send_json({
                    "type": "tool_start",
                    "tool_name": name or "tool",
                    "display": f"Running {name or 'tool'}…",
                })
            elif etype == "on_tool_end":
                await websocket.send_json({
                    "type": "tool_end",
                    "tool_name": name or "tool",
                })
            elif etype == "on_chat_model_stream":
                chunk = data.get("chunk")
                content = getattr(chunk, "content", "") if chunk is not None else ""
                # Only stream tokens from the editor pass to avoid leaking
                # internal reasoning / classifier tokens.
                tags = event.get("tags") or []
                metadata = event.get("metadata") or {}
                node = metadata.get("langgraph_node") or ""
                if node == "editor" or "editor" in tags:
                    if content:
                        await websocket.send_json({"type": "token", "content": content})
                        streamed_any_token = True
            elif etype == "on_custom_event" and name == "chart_svg":
                chart_svg = data
                await websocket.send_json({"type": "chart_svg", "svg": data})
            elif etype == "on_custom_event" and name == "structured_card":
                structured_card = data
                await websocket.send_json({
                    "type": "structured_card",
                    "card_type": (data or {}).get("card_type", "info") if isinstance(data, dict) else "info",
                    "data": data if isinstance(data, dict) else {"value": data},
                })
            elif etype == "on_chain_end" and name == "response":
                output = data.get("output") or {}
                draft = (output or {}).get("draft_response") or ""
                if draft:
                    final_text = draft

        # Inspect graph state for interrupts (sensitive turn)
        snapshot = agent_graph.get_state(config)
        snapshot_values = snapshot.values if hasattr(snapshot, "values") else {}
        if snapshot_values.get("awaiting_confirmation") and snapshot_values.get("sensitive_flag"):
            preview = snapshot_values.get("confirmation_preview") or final_text or "Want me to continue?"
            await websocket.send_json({"type": "confirmation_required", "preview": preview})
            interrupted = True
            return

        # If we never streamed any token (eg. no editor pass), send the final
        # text as a single token frame so the client always receives content.
        if not streamed_any_token and final_text:
            await websocket.send_json({"type": "token", "content": final_text})

        await websocket.send_json({"type": "done"})

        # Persist assistant message
        if final_text:
            try:
                await create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=final_text,
                    language=initial_state.get("language"),
                )
            except Exception as exc:
                logger.warning("Failed to persist assistant message: %s", exc)

    except WebSocketDisconnect:
        # Client disconnected mid-turn — do NOT persist a partial message.
        raise
    except Exception as exc:
        logger.exception("Agent error")
        try:
            await websocket.send_json({"type": "error", "message": _redact(str(exc))})
        except Exception:
            pass
    finally:
        # If a sensitive interrupt occurred, do not emit done here.
        _ = interrupted


async def _resume_with_confirmation(
    websocket: WebSocket,
    thread_id: str,
    confirmed: bool,
    conversation_id: str,
    language: str,
) -> None:
    """Resume the graph after a HiTL interrupt."""
    config = {"configurable": {"thread_id": thread_id}}

    if not confirmed:
        # Skip the editor entirely; emit a single canned redirect.
        canned = {
            "en": "Understood — let's set that aside. How else can I help?",
            "hi": "ठीक है, उसे फिर कभी देखेंगे। और किस बारे में बात करें?",
            "mr": "ठीक आहे, ते आपण नंतर पाहू. आणखी कशात मदत करू?",
            "gu": "સારું, એ પછી જોઈશું. બીજું શું મદદ કરું?",
            "ta": "சரி, அதை பின்பு பார்க்கலாம். வேறு என்ன உதவ வேண்டும்?",
            "kn": "ಸರಿ, ಅದನ್ನು ನಂತರ ನೋಡೋಣ. ಬೇರೆ ಏನಾದರೂ ಸಹಾಯ ಬೇಕೆ?",
        }.get(language, "Understood — let's set that aside.")
        await websocket.send_json({"type": "token", "content": canned})
        await websocket.send_json({"type": "done"})
        try:
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=canned,
                language=language,
            )
        except Exception:
            pass
        return

    # Resume into the editor pass.
    try:
        # langgraph >= 0.2 supports Command(resume=...).
        from langgraph.types import Command  # type: ignore

        resumed_iter = agent_graph.astream_events(
            Command(resume={"confirmed": True}), config=config, version="v2"
        )
    except Exception:
        # Fallback: inject confirmed=True via update_state.
        agent_graph.update_state(config, {"confirmed": True})
        resumed_iter = agent_graph.astream_events(None, config=config, version="v2")

    final_text = ""
    streamed_any_token = False
    async for event in resumed_iter:
        etype = event.get("event")
        data = event.get("data") or {}
        name = event.get("name")
        metadata = event.get("metadata") or {}
        node = metadata.get("langgraph_node") or ""

        if etype == "on_chat_model_stream" and (node == "editor" or "editor" in (event.get("tags") or [])):
            chunk = data.get("chunk")
            content = getattr(chunk, "content", "") if chunk is not None else ""
            if content:
                await websocket.send_json({"type": "token", "content": content})
                streamed_any_token = True
        elif etype == "on_chain_end" and name == "response":
            output = data.get("output") or {}
            draft = (output or {}).get("draft_response") or ""
            if draft:
                final_text = draft

    if not streamed_any_token and final_text:
        await websocket.send_json({"type": "token", "content": final_text})

    await websocket.send_json({"type": "done"})
    if final_text:
        try:
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                language=language,
            )
        except Exception:
            pass


# ── WebSocket Chat Endpoint ─────────────────────────────────────


@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint — full Phase 4 protocol."""
    await websocket.accept()
    user = await _authenticate_or_close(websocket)
    if not user:
        return

    natal_chart, active_dashas, profile_id = await _load_self_profile(user["id"])

    try:
        conversation = await create_conversation(
            user_id=user["id"],
            profile_id=profile_id,
            title="Chat session",
        )
        conversation_id = conversation["id"]
    except Exception:
        conversation_id = f"local:{session_id}"

    thread_id = f"{user['id']}:{conversation_id}"
    last_language = user.get("default_language") or "en"

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except Exception:
                continue
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "confirmation":
                confirmed = bool(data.get("confirmed", False))
                await _resume_with_confirmation(
                    websocket, thread_id, confirmed, conversation_id, last_language
                )
                continue

            if msg_type != "message":
                continue

            content = (data.get("content") or "").strip()
            language = data.get("language") or user.get("default_language") or "en"
            last_language = language
            if not content:
                continue

            # Persist user message
            try:
                await create_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=content,
                    language=language,
                )
            except Exception:
                pass

            initial_state = _initial_state(
                user,
                session_id,
                content,
                language,
                natal_chart,
                active_dashas,
            )
            await _stream_agent_turn(websocket, thread_id, initial_state, conversation_id)

    except WebSocketDisconnect:
        return
    except Exception as exc:
        logger.exception("Connection error")
        try:
            await websocket.send_json({"type": "error", "message": _redact(str(exc))})
        except Exception:
            pass
