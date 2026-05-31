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
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.agent.graph import agent_graph
from app.agent._event_bus import bus
from app.agent._user_context import set_request_context
from app.db.queries import (
    create_conversation,
    create_message,
    get_self_profile,
    get_profiles_by_user,
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


IST = ZoneInfo("Asia/Kolkata")


async def _load_self_profile(user_id: str):
    try:
        profile = await get_self_profile(user_id)
    except Exception:
        profile = None
    if not profile:
        return None, None, None, None
    return (
        profile.get("computed_chart"),
        profile.get("computed_dashas"),
        profile.get("id"),
        profile,
    )


async def _load_family_summary(user_id: str, self_profile_id: str | None) -> list[dict]:
    """List of {id, name, relationship, has_chart} for every saved profile (excluding self)."""
    try:
        rows = await get_profiles_by_user(user_id)
    except Exception:
        return []
    out: list[dict] = []
    for row in rows or []:
        if self_profile_id and row.get("id") == self_profile_id:
            continue
        out.append({
            "id": row.get("id"),
            "name": row.get("name"),
            "relationship": row.get("relationship"),
            "has_chart": bool(row.get("computed_chart")),
            "birth_date": row.get("birth_date"),
            "place_name": row.get("place_name"),
        })
    return out


def _ist_now_payload() -> dict:
    now = datetime.now(IST)
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
        "timezone": "Asia/Kolkata",
    }


def _user_birth_payload(self_profile: dict | None) -> dict | None:
    if not self_profile:
        return None
    return {
        "name": self_profile.get("name"),
        "relationship": self_profile.get("relationship"),
        "birth_date": self_profile.get("birth_date"),
        "birth_time": self_profile.get("birth_time"),
        "place_name": self_profile.get("place_name"),
        "lat": self_profile.get("lat"),
        "lng": self_profile.get("lng"),
        "timezone": self_profile.get("timezone"),
    }


def _user_residence_payload(user: dict) -> dict | None:
    place = user.get("residence_place_name")
    lat = user.get("residence_lat")
    lng = user.get("residence_lng")
    tz = user.get("residence_timezone")
    if not (place and lat is not None and lng is not None and tz):
        return None
    return {"place_name": place, "lat": lat, "lng": lng, "timezone": tz}


def _initial_state(
    user: dict,
    content: str,
    language: str,
    natal_chart,
    active_dashas,
    self_birth: dict | None,
    residence: dict | None,
    family_summary: list[dict],
) -> dict:
    return {
        "messages": [HumanMessage(content=content)],
        "user_id": user["id"],
        "session_id": user["id"],
        "language": language or user.get("default_language") or "en",
        "natal_chart": natal_chart or {},
        "active_dashas": active_dashas or {},
        "self_birth": self_birth or {},
        "residence": residence or {},
        "family_summary": family_summary or [],
        "user_name": user.get("name") or "",
        "chart_format": user.get("chart_format") or "south_indian",
        "now_ist": _ist_now_payload(),
        "intent": "",
        "tool_outputs": [],
        "sensitive_flag": False,
        "awaiting_confirmation": False,
        "confirmed": False,
    }


def _truncate_reply(text: str, max_chars: int = 4000) -> str:
    """
    Defensively cap an overly long assistant reply.

    Even with a strict prompt the model occasionally regurgitates an
    entire tool-output payload (we've seen 600k-character replies from
    raw Muhurta/Panchang dumps). Cap them here so the database, the
    network, and the chat UI never have to swallow them. The visible
    cap is about a page of text, plus a short note pointing the seeker
    at the visual card.
    """
    if not isinstance(text, str):
        return text
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rstrip()
    return (
        truncated
        + "\n\n_…the full details are in the card above._"
    )


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
        "final_text": _truncate_reply(final_text),
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
    natal_chart, active_dashas, self_profile_id, self_profile = await _load_self_profile(user["id"])
    family_summary = await _load_family_summary(user["id"], self_profile_id)
    self_birth = _user_birth_payload(self_profile)
    residence = _user_residence_payload(user)

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
    initial = _initial_state(
        user, content, language, natal_chart, active_dashas,
        self_birth=self_birth, residence=residence, family_summary=family_summary,
    )

    with set_request_context(
        user_id=user["id"],
        natal_chart=natal_chart,
        chart_format=user.get("chart_format") or "south_indian",
    ):
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
            persisted_payload: dict | None = None
            runs = result["tool_runs"]
            cards = result["cards"]
            svg = result["chart_svg"]
            if runs or cards or svg:
                persisted_payload = {}
                if runs:
                    persisted_payload["runs"] = runs
                if cards:
                    persisted_payload["cards"] = cards
                if svg:
                    persisted_payload["chart_svg"] = svg
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                language=language,
                tool_calls=persisted_payload,
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

    with set_request_context(
        user_id=user["id"],
        natal_chart=None,  # set on resume from snapshot if needed
        chart_format=user.get("chart_format") or "south_indian",
    ):
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
            persisted_payload: dict | None = None
            runs = result["tool_runs"]
            cards = result["cards"]
            svg = result["chart_svg"]
            if runs or cards or svg:
                persisted_payload = {}
                if runs:
                    persisted_payload["runs"] = runs
                if cards:
                    persisted_payload["cards"] = cards
                if svg:
                    persisted_payload["chart_svg"] = svg
            await create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_text,
                language=language,
                tool_calls=persisted_payload,
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
