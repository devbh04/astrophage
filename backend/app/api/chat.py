"""
HTTP chat API.

`POST /api/chat` runs the agent and returns the final result (text + cards +
chart svg) in one response. `POST /api/chat/{conversation_id}/confirm`
resumes a sensitive turn.

Tool activity (``tool_start`` / ``tool_end``) is published to the user's
event-bus channel so the live WebSocket indicator can render them while
the HTTP request is in flight.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.agent.graph import agent_graph
from app.agent._event_bus import bus
from app.db.queries import (
    create_conversation,
    create_message,
    get_self_profile,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    content: str
    conversation_id: str | None = None
    language: str | None = None


class ChatCard(BaseModel):
    card_type: str
    data: dict[str, Any]


class ChatToolRun(BaseModel):
    tool: str
    args: Any | None = None
    status: str = "ok"  # "ok" | "running" | "error"


class ChatResponse(BaseModel):
    conversation_id: str
    content: str
    cards: list[ChatCard] = []
    chart_svg: str | None = None
    tool_runs: list[ChatToolRun] = []
    sensitive: bool = False
    confirmation_preview: str | None = None
    error: str | None = None


class ConfirmRequest(BaseModel):
    confirmed: bool


# ── Helpers ─────────────────────────────────────────────────────


async def _load_self_profile(user_id: str):
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
    content: str,
    language: str,
    natal_chart,
    active_dashas,
) -> dict:
    return {
        "messages": [HumanMessage(content=content)],
        "user_id": user["id"],
        "session_id": user["id"],
        "language": language or user.get("default_language") or "en",
        "natal_chart": natal_chart or {},
        "active_dashas": active_dashas or {},
        "intent": "",
        "tool_outputs": [],
        "sensitive_flag": False,
        "awaiting_confirmation": False,
        "confirmed": False,
    }


async def _run_turn(
    *,
    user_id: str,
    initial: dict | Any,
    config: dict,
) -> dict:
    """
    Invoke the agent graph. Publish tool_start/tool_end to the event bus
    keyed by user_id. Return the final draft + structured artifacts +
    the list of tools that were invoked during the turn.
    """
    final_text = ""
    cards: list[dict[str, Any]] = []
    chart_svg: str | None = None
    tool_runs: list[dict[str, Any]] = []
    started = time.monotonic()

    try:
        async for event in agent_graph.astream_events(initial, config=config, version="v2"):
            etype = event.get("event")
            data = event.get("data") or {}
            name = event.get("name")

            if etype == "on_tool_start":
                # LangChain-native tool runs (not currently used by our manual
                # TOOL_REGISTRY dispatcher, but kept for forwards-compat).
                logger.info("→ tool_start: %s", name)
                bus.publish(user_id, {"type": "tool_start", "tool_name": name or "tool"})
                tool_runs.append({
                    "tool": name or "tool",
                    "args": data.get("input") if isinstance(data, dict) else None,
                    "status": "running",
                })
            elif etype == "on_tool_end":
                logger.info("← tool_end:   %s", name)
                bus.publish(user_id, {"type": "tool_end", "tool_name": name or "tool"})
                for run in reversed(tool_runs):
                    if run.get("tool") == name and run.get("status") == "running":
                        run["status"] = "ok"
                        break
            elif etype == "on_custom_event" and name == "tool_run_start":
                # Emitted by tool_executor_node before each registry call.
                payload = data if isinstance(data, dict) else {}
                tool_name = payload.get("tool") or "tool"
                logger.info("→ tool_run_start: %s", tool_name)
                bus.publish(user_id, {"type": "tool_start", "tool_name": tool_name})
                tool_runs.append({
                    "tool": tool_name,
                    "args": payload.get("args"),
                    "status": "running",
                })
            elif etype == "on_custom_event" and name == "tool_run_end":
                payload = data if isinstance(data, dict) else {}
                tool_name = payload.get("tool") or "tool"
                ok = bool(payload.get("ok", True))
                logger.info("← tool_run_end:   %s (ok=%s)", tool_name, ok)
                bus.publish(user_id, {"type": "tool_end", "tool_name": tool_name})
                for run in reversed(tool_runs):
                    if run.get("tool") == tool_name and run.get("status") == "running":
                        run["status"] = "ok" if ok else "error"
                        break
            elif etype == "on_custom_event" and name == "chart_svg":
                if isinstance(data, str) and data.strip():
                    chart_svg = data
            elif etype == "on_custom_event" and name == "structured_card":
                if isinstance(data, dict):
                    cards.append({
                        "card_type": data.get("card_type", "info"),
                        "data": data.get("data", {}),
                    })
            elif etype == "on_chain_end" and name == "response":
                output = data.get("output") or {}
                draft = (output or {}).get("draft_response") or ""
                if draft:
                    final_text = draft
    except Exception as exc:
        logger.exception("Agent error")
        return {
            "final_text": "",
            "cards": cards,
            "chart_svg": chart_svg,
            "tool_runs": tool_runs,
            "error": str(exc),
            "sensitive": False,
            "preview": "",
        }

    # Fallback: if for any reason on_chain_end for "response" wasn't seen,
    # pull draft_response straight from the saved graph state.
    if not final_text:
        try:
            snapshot = agent_graph.get_state(config)
            sv = getattr(snapshot, "values", {}) or {}
            final_text = sv.get("draft_response", "") or ""
        except Exception:
            pass

    snapshot = agent_graph.get_state(config)
    snapshot_values = getattr(snapshot, "values", {}) or {}
    sensitive = bool(
        snapshot_values.get("awaiting_confirmation")
        and snapshot_values.get("sensitive_flag")
    )
    preview = snapshot_values.get("confirmation_preview") or ""

    elapsed = time.monotonic() - started
    logger.info(
        "turn finished in %.1fs · tools=%d cards=%d svg=%s text=%dch",
        elapsed,
        len(tool_runs),
        len(cards),
        bool(chart_svg),
        len(final_text or ""),
    )

    return {
        "final_text": final_text,
        "cards": cards,
        "chart_svg": chart_svg,
        "tool_runs": tool_runs,
        "error": None,
        "sensitive": sensitive,
        "preview": preview,
    }


# ── Endpoints ───────────────────────────────────────────────────


@router.post("", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
):
    content = (body.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty message")

    logger.info("chat ▷ user=%s msg=%r", user.get("email", user["id"]), content[:80])
    language = body.language or user.get("default_language") or "en"
    natal_chart, active_dashas, self_profile_id = await _load_self_profile(user["id"])

    # Lazy conversation creation
    conversation_id = body.conversation_id
    if not conversation_id:
        try:
            conv = await create_conversation(
                user_id=user["id"],
                profile_id=self_profile_id,
                title=content[:50],
            )
            conversation_id = conv["id"]
        except Exception as exc:
            logger.exception("Failed to create conversation")
            raise HTTPException(status_code=500, detail=f"create_conversation failed: {exc}")

    # Persist user message
    try:
        await create_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            language=language,
        )
    except Exception as exc:
        logger.warning("Failed to persist user message: %s", exc)

    thread_id = f"{user['id']}:{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}
    initial = _initial_state(user, content, language, natal_chart, active_dashas)

    result = await _run_turn(user_id=user["id"], initial=initial, config=config)

    if result["error"]:
        return ChatResponse(
            conversation_id=conversation_id,
            content="",
            cards=[ChatCard(**c) for c in result["cards"]],
            chart_svg=result["chart_svg"],
            tool_runs=[ChatToolRun(**r) for r in result["tool_runs"]],
            error=result["error"],
        )

    if result["sensitive"]:
        return ChatResponse(
            conversation_id=conversation_id,
            content="",
            cards=[ChatCard(**c) for c in result["cards"]],
            chart_svg=result["chart_svg"],
            tool_runs=[ChatToolRun(**r) for r in result["tool_runs"]],
            sensitive=True,
            confirmation_preview=result["preview"] or "Continue?",
        )

    final_text = result["final_text"]
    if final_text:
        try:
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                language=language,
                tool_calls={"runs": result["tool_runs"]} if result["tool_runs"] else None,
            )
        except Exception as exc:
            logger.warning("Failed to persist assistant message: %s", exc)

    return ChatResponse(
        conversation_id=conversation_id,
        content=final_text,
        cards=[ChatCard(**c) for c in result["cards"]],
        chart_svg=result["chart_svg"],
        tool_runs=[ChatToolRun(**r) for r in result["tool_runs"]],
    )


@router.post("/{conversation_id}/confirm", response_model=ChatResponse)
async def confirm(
    conversation_id: str,
    body: ConfirmRequest,
    user: dict = Depends(get_current_user),
):
    """Resume a sensitive turn after the user confirmed (or declined)."""
    language = user.get("default_language") or "en"
    thread_id = f"{user['id']}:{conversation_id}"
    config = {"configurable": {"thread_id": thread_id}}

    if not body.confirmed:
        canned = {
            "en": "Understood — let's set that aside. How else can I help?",
            "hi": "ठीक है, उसे फिर कभी देखेंगे।",
            "mr": "ठीक आहे, ते आपण नंतर पाहू.",
            "gu": "સારું, એ પછી જોઈશું.",
            "ta": "சரி, அதை பின்பு பார்க்கலாம்.",
            "kn": "ಸರಿ, ಅದನ್ನು ನಂತರ ನೋಡೋಣ.",
        }.get(language, "Understood — let's set that aside.")
        try:
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=canned,
                language=language,
            )
        except Exception:
            pass
        return ChatResponse(conversation_id=conversation_id, content=canned)

    # Resume into the editor pass.
    try:
        from langgraph.types import Command  # type: ignore

        resume_input: Any = Command(resume={"confirmed": True})
    except Exception:
        agent_graph.update_state(config, {"confirmed": True})
        resume_input = None

    result = await _run_turn(user_id=user["id"], initial=resume_input, config=config)

    if result["error"]:
        return ChatResponse(
            conversation_id=conversation_id,
            content="",
            cards=[ChatCard(**c) for c in result["cards"]],
            chart_svg=result["chart_svg"],
            tool_runs=[ChatToolRun(**r) for r in result["tool_runs"]],
            error=result["error"],
        )

    final_text = result["final_text"]
    if final_text:
        try:
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                language=language,
                tool_calls={"runs": result["tool_runs"]} if result["tool_runs"] else None,
            )
        except Exception:
            pass

    return ChatResponse(
        conversation_id=conversation_id,
        content=final_text,
        cards=[ChatCard(**c) for c in result["cards"]],
        chart_svg=result["chart_svg"],
        tool_runs=[ChatToolRun(**r) for r in result["tool_runs"]],
    )
