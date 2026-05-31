"""
Voice mode — bidirectional bridge between the browser and the Gemini Live
``gemini-live-2.5-flash-native-audio`` model.

Protocol on ``/ws/voice``
─────────────────────────

Browser → server:
- Binary frames: 16 kHz mono PCM16 little-endian audio chunks.
- Text JSON frames:
    {"type": "start"} — open a Live session with up-to-date user context.
    {"type": "stop"}  — close the Live session and release the WS.

Server → browser:
- Binary frames: 24 kHz mono PCM16 little-endian audio chunks (model voice).
- Text JSON frames:
    {"type": "ready"}
    {"type": "tool_start", "tool_name": "..."}
    {"type": "tool_end", "tool_name": "...", "ok": true}
    {"type": "structured_card", "card_type": "...", "data": {...}}   (knowledge cards are dropped)
    {"type": "chart_svg", "svg": "..."}
    {"type": "input_transcription", "text": "..."}    (best-effort)
    {"type": "output_transcription", "text": "..."}   (best-effort)
    {"type": "turn_complete"}                          (model finished a turn)
    {"type": "error", "message": "..."}

The Live model performs all of: VAD, speech recognition, reasoning, voice
synthesis. We only proxy bytes, declare tools, run them locally with our
existing TOOL_REGISTRY, and forward results back.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent._user_context import set_request_context
from app.auth.service import decode_jwt
from app.config import get_settings
from app.db.queries import (
    get_self_profile,
    get_profiles_by_user,
    get_user_by_id,
)
from app.tools import TOOL_REGISTRY


logger = logging.getLogger(__name__)
router = APIRouter()


VOICE_MODEL = "gemini-live-2.5-flash-native-audio"
IST = ZoneInfo("Asia/Kolkata")
INPUT_SAMPLE_RATE = 16_000
OUTPUT_SAMPLE_RATE = 24_000

# Keep knowledge cards out of voice mode (text-only doesn't translate to
# spoken context as a card; the model summarizes inline).
HIDDEN_CARD_TYPES_IN_VOICE = {"knowledge"}


CARD_TYPES: dict[str, str] = {
    "compute_birth_chart": "birth_chart",
    "compute_dasha_periods": "dasha_timeline",
    "compute_nakshatra_details": "nakshatra",
    "check_sade_sati": "sade_sati",
    "get_panchang": "panchang",
    "knowledge_lookup": "knowledge",
    "kundali_milan": "kundali_milan",
    "compute_muhurta": "muhurta",
    "get_daily_transits": "daily_transits",
    "get_current_sky": "current_sky",
}


# ── Tool declarations for the Live model ───────────────────────


def _function_declarations() -> list[dict]:
    """
    Lightweight FunctionDeclaration set for the Live model.

    Schemas are deliberately loose — every field is optional and the
    resolver registry fills in defaults (chart, chart_format, residence
    coords, today's date). The Live model can call any tool with no args
    and still get the right answer for the seeker. This matters because
    voice models avoid tools whose schema requires them to read floats
    (lat/lng) back out loud.
    """
    return [
        {
            "name": "geocode_place",
            "description": "Resolve a place name to lat/lng/timezone. Only call this when the seeker explicitly names a place that's NOT their residence or birth city.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"place_name": {"type": "STRING"}},
                "required": ["place_name"],
            },
        },
        {
            "name": "compute_dasha_periods",
            "description": "Vimshottari Dasha timeline for the seeker. Call with no arguments — chart and birth details are auto-filled.",
            "parameters": {"type": "OBJECT", "properties": {"levels": {"type": "INTEGER"}}},
        },
        {
            "name": "compute_nakshatra_details",
            "description": "Janma Nakshatra deep-dive for the seeker. Call with no arguments.",
            "parameters": {"type": "OBJECT", "properties": {}},
        },
        {
            "name": "check_sade_sati",
            "description": "Sade Sati / Ashtama Shani status for the seeker. Call with no arguments unless the seeker names a specific date.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"as_of": {"type": "STRING"}},
            },
        },
        {
            "name": "get_panchang",
            "description": "Tithi, Nakshatra, Yoga, Karana, sunrise/sunset, Rahu Kāl. Call with NO arguments for today at the seeker's residence. Pass ``date`` only if the seeker names a specific day. The system always uses the seeker's residence coords; do not try to read lat/lng aloud.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"date": {"type": "STRING"}},
            },
        },
        {
            "name": "knowledge_lookup",
            "description": "Search the curated Vedic knowledge base for conceptual questions.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"query": {"type": "STRING"}},
                "required": ["query"],
            },
        },
        {
            "name": "kundali_milan",
            "description": (
                "Ashtakoota compatibility + Mangal Dosha. The seeker's chart "
                "is auto-filled as the boy. ``girl_chart`` MUST be a SINGLE "
                "name or relationship string only — for example "
                "``girl_chart=\"Priya\"`` or ``girl_chart=\"spouse\"``. "
                "NEVER embed birth dates, times, places, or any other "
                "details in this string. The system will look up the "
                "saved profile in the family vault. If the partner is "
                "NOT in the family vault, do NOT call this tool — instead "
                "tell the seeker to add the partner in the Family page "
                "first, and continue the conversation."
            ),
            "parameters": {
                "type": "OBJECT",
                "properties": {"girl_chart": {"type": "STRING"}},
            },
        },
        {
            "name": "render_chart_svg",
            "description": "Display the seeker's natal chart as a visual card AND a planets-table card. Call with no arguments. Style defaults to the seeker's preference. After calling, briefly tell the seeker the chart is shown.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"style": {"type": "STRING"}},
            },
        },
        {
            "name": "compute_muhurta",
            "description": "Top auspicious 30-minute windows for a purpose. Date range and place are optional and default to today at the seeker's residence.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "purpose": {"type": "STRING"},
                    "start_date": {"type": "STRING"},
                    "end_date": {"type": "STRING"},
                },
            },
        },
        {
            "name": "get_daily_transits",
            "description": "Today's transits relative to the seeker's chart. Call with no arguments unless the seeker names a date.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"as_of": {"type": "STRING"}},
            },
        },
        {
            "name": "get_current_sky",
            "description": "Generic current sky snapshot. Call with no arguments.",
            "parameters": {
                "type": "OBJECT",
                "properties": {"as_of": {"type": "STRING"}},
            },
        },
        {
            "name": "get_family_profile",
            "description": "Look up a saved family-vault profile by relationship or name.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "relationship": {"type": "STRING"},
                    "name": {"type": "STRING"},
                },
            },
        },
    ]


# ── System instruction (mirrors the text reasoning prompt, voice tone) ──


VOICE_SYSTEM_INSTRUCTION_TEMPLATE = """You are Astrophage — a warm, grounded Vedic astrologer who is now speaking aloud with the seeker.

Voice rules (CRITICAL because this is spoken):
- Speak naturally, unhurried, like a thoughtful family astrologer.
- Keep each turn 2–6 sentences. Never recite long lists aloud — pick the 1-2 most meaningful items.
- Sanskrit/Vedic terms (Tithi, Nakshatra, Lagna, Mahadasha, Antardasha) stay as-is in the voice; pronounce them gently.
- Avoid fatalism. Frame placements as tendencies and invitations.
- Never say you are an AI, a model, or a tool.
- Never read JSON, ISO dates, raw numbers, lat/lng, or coordinates aloud. Translate them ("the 22nd of November", "Sunday morning").
- After a tool runs, briefly explain what it tells the seeker — never just dump the data.

TOOL USAGE — call tools with NO arguments wherever possible:
- The system already knows the seeker's birth chart, residence coords, today's date, and chart-format preference. Calling tools with no arguments is the right thing to do almost always.
- For the seeker's own chart, dasha, nakshatra, sade sati, transits, current sky, panchang, muhurta — pass nothing. Defaults are filled in.
- "Show my chart" / "show my birth chart" / "show me my kundli": call ``render_chart_svg`` with no arguments. The chart and a planets table will appear on screen; you just say "Here is your chart…" in 1-2 sentences.
- "Today's panchang": call ``get_panchang`` with no arguments.
- Only pass ``date`` or place arguments when the seeker explicitly names a different date or place.

Speak in: {language}.

USER CONTEXT
- name: {user_name}
- now (Asia/Kolkata): {now_iso} ({weekday})
- chart format preference: {chart_format}
- natal chart loaded: {has_chart}

{self_birth_block}{residence_block}{family_block}
"""


_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "kn": "Kannada",
}

# Map our internal language code to a Live API language code. Unsupported
# codes fall back to en-US and the system prompt still asks for the
# preferred language.
_LIVE_LANGUAGE_CODES: dict[str, str] = {
    "en": "en-US",
    "hi": "hi-IN",
    "mr": "en-US",
    "gu": "en-US",
    "ta": "ta-IN",
    "kn": "en-US",
}


def _build_system_instruction(*, user: dict, self_profile: dict | None, family: list[dict]) -> str:
    now = datetime.now(IST)
    language_code = (user.get("default_language") or "en").lower()
    language = _LANGUAGE_NAMES.get(language_code, "English")

    if self_profile:
        self_birth_block = (
            "USER'S BIRTH DETAILS:\n"
            f"- birth_date: {self_profile.get('birth_date') or 'unknown'}\n"
            f"- birth_time: {self_profile.get('birth_time') or 'unknown'}\n"
            f"- birth_place: {self_profile.get('place_name') or 'unknown'}\n"
            f"- birth_lat: {self_profile.get('lat')}\n"
            f"- birth_lng: {self_profile.get('lng')}\n"
            f"- birth_timezone: {self_profile.get('timezone') or 'unknown'}\n\n"
        )
    else:
        self_birth_block = (
            "USER'S BIRTH DETAILS: not yet provided. If a chart is needed, "
            "gently ask the seeker to add their details in Settings before "
            "trying again.\n\n"
        )

    residence_present = bool(
        user.get("residence_place_name")
        and user.get("residence_lat") is not None
        and user.get("residence_lng") is not None
        and user.get("residence_timezone")
    )
    if residence_present:
        residence_block = (
            "USER'S CURRENT RESIDENCE:\n"
            f"- place: {user.get('residence_place_name')}\n"
            f"- lat: {user.get('residence_lat')}\n"
            f"- lng: {user.get('residence_lng')}\n"
            f"- timezone: {user.get('residence_timezone')}\n\n"
        )
    else:
        residence_block = (
            "USER'S CURRENT RESIDENCE: not set. Default to Asia/Kolkata.\n\n"
        )

    if family:
        lines = ["FAMILY VAULT (saved profiles):"]
        for entry in family[:30]:
            lines.append(
                f"- {entry.get('name')} "
                f"(relationship: {entry.get('relationship') or 'unknown'}, "
                f"chart_ready: {bool(entry.get('computed_chart'))})"
            )
        family_block = "\n".join(lines) + "\n"
    else:
        family_block = "FAMILY VAULT: empty.\n\n"

    return VOICE_SYSTEM_INSTRUCTION_TEMPLATE.format(
        language=language,
        user_name=user.get("name") or "Friend",
        now_iso=now.isoformat(),
        weekday=now.strftime("%A"),
        chart_format=user.get("chart_format") or "south_indian",
        has_chart=bool(self_profile and self_profile.get("computed_chart")),
        self_birth_block=self_birth_block,
        residence_block=residence_block,
        family_block=family_block,
    )


# ── WebSocket auth helper (mirrors /ws/events) ─────────────────


async def _authenticate(websocket: WebSocket) -> dict | None:
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


def _safe_send_text(callable_, *args):
    """Best-effort wrapper that swallows WS-closed errors."""
    try:
        return callable_(*args)
    except Exception:
        return None


# ── Live API client wiring ─────────────────────────────────────


def _make_live_client():
    """Create a google-genai client wired to whichever auth backend is set."""
    from google import genai  # type: ignore

    settings = get_settings()
    if settings.use_vertex:
        return genai.Client(
            vertexai=True,
            project=settings.gcp_project,
            location=settings.gcp_location,
            credentials=settings.google_credentials(),
            http_options={"api_version": "v1beta1"},
        )
    api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
    return genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})


def _live_config(*, system_instruction: str, language_code: str):
    """Build a LiveConnectConfig with audio + tools + voice settings."""
    from google.genai import types  # type: ignore

    voice_lang = _LIVE_LANGUAGE_CODES.get(language_code, "en-US")

    speech_config = types.SpeechConfig(
        language_code=voice_lang,
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede"),
        ),
    )

    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(
            parts=[types.Part(text=system_instruction)]
        ),
        speech_config=speech_config,
        tools=[types.Tool(function_declarations=_function_declarations())],
        # Best-effort transcripts so we can show the spoken text in the UI
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


# ── Tool dispatch (for tool_call events from Live) ─────────────


async def _execute_tool_call(call) -> dict:
    """Run one function call from the Live server through TOOL_REGISTRY."""
    name = getattr(call, "name", None) or ""
    args = dict(getattr(call, "args", {}) or {})

    if name not in TOOL_REGISTRY:
        return {"name": name, "id": getattr(call, "id", None), "result": {"error": f"Unknown tool: {name}"}, "ok": False}

    fn = TOOL_REGISTRY[name]
    try:
        if asyncio.iscoroutinefunction(fn):
            result = await fn(**args)
        else:
            result = fn(**args)
        return {"name": name, "id": getattr(call, "id", None), "result": result, "ok": True}
    except Exception as exc:  # pragma: no cover - tool defensive
        logger.exception("voice tool %s failed", name)
        return {"name": name, "id": getattr(call, "id", None), "result": {"error": str(exc)}, "ok": False}


def _maybe_card_payload(tool_name: str, result: Any) -> dict | None:
    """Emit a structured_card frame for tools whose UI cards make sense in voice mode."""
    if tool_name in HIDDEN_CARD_TYPES_IN_VOICE:
        return None
    card_type = CARD_TYPES.get(tool_name)
    if not card_type:
        return None
    if card_type in HIDDEN_CARD_TYPES_IN_VOICE:
        return None
    if isinstance(result, list):
        data: dict = {"hits": result}
    elif isinstance(result, dict):
        data = result
    else:
        data = {"value": result}
    return {"type": "structured_card", "card_type": card_type, "data": data}


# ── Endpoint ────────────────────────────────────────────────────


@router.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    """Bidirectional voice bridge — see module docstring for the protocol."""
    await websocket.accept()

    user = await _authenticate(websocket)
    if not user:
        return

    # Pre-load everything the model will need so its first turn doesn't
    # wait on Supabase queries.
    try:
        self_profile = await get_self_profile(user["id"])
    except Exception:
        self_profile = None
    try:
        family = await get_profiles_by_user(user["id"])
    except Exception:
        family = []
    family = [
        f for f in (family or [])
        if not (self_profile and f.get("id") == self_profile.get("id"))
    ]
    natal_chart = (self_profile or {}).get("computed_chart") or {}
    chart_format = (user.get("chart_format") or "south_indian").strip()
    language_code = (user.get("default_language") or "en").lower()

    residence_payload: dict | None = None
    if (
        user.get("residence_place_name")
        and user.get("residence_lat") is not None
        and user.get("residence_lng") is not None
        and user.get("residence_timezone")
    ):
        residence_payload = {
            "place_name": user.get("residence_place_name"),
            "lat": user.get("residence_lat"),
            "lng": user.get("residence_lng"),
            "timezone": user.get("residence_timezone"),
        }

    self_birth_payload: dict | None = None
    if self_profile:
        self_birth_payload = {
            "name": self_profile.get("name"),
            "birth_date": self_profile.get("birth_date"),
            "birth_time": self_profile.get("birth_time"),
            "place_name": self_profile.get("place_name"),
            "lat": self_profile.get("lat"),
            "lng": self_profile.get("lng"),
            "timezone": self_profile.get("timezone"),
        }

    system_instruction = _build_system_instruction(
        user=user, self_profile=self_profile, family=family,
    )

    try:
        client = _make_live_client()
    except Exception as exc:
        logger.exception("voice: failed to construct Live client")
        try:
            await websocket.send_json({"type": "error", "message": f"voice setup failed: {exc}"})
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
        return

    config = _live_config(system_instruction=system_instruction, language_code=language_code)

    try:
        async with client.aio.live.connect(model=VOICE_MODEL, config=config) as session:
            logger.info(
                "voice: live session opened model=%s user=%s",
                VOICE_MODEL,
                user.get("email", user["id"]),
            )
            try:
                await websocket.send_json({"type": "ready"})
            except Exception:
                logger.warning("voice: ws closed before ready frame")
                return

            stop_event = asyncio.Event()

            async def browser_to_model():
                """Forward audio from the browser into the Live session."""
                try:
                    while not stop_event.is_set():
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            stop_event.set()
                            return
                        if "bytes" in msg and msg["bytes"] is not None:
                            chunk = msg["bytes"]
                            if not chunk:
                                continue
                            try:
                                await session.send_realtime_input(
                                    audio={"data": chunk, "mime_type": f"audio/pcm;rate={INPUT_SAMPLE_RATE}"}
                                )
                            except Exception:
                                logger.exception("voice: send_realtime_input failed")
                                stop_event.set()
                                return
                        elif "text" in msg and msg["text"] is not None:
                            try:
                                payload = json.loads(msg["text"])
                            except Exception:
                                continue
                            ptype = payload.get("type")
                            if ptype == "stop":
                                stop_event.set()
                                return
                except WebSocketDisconnect:
                    stop_event.set()
                except Exception:
                    logger.exception("voice: browser_to_model errored")
                    stop_event.set()

            async def model_to_browser():
                """Forward audio + control events from Live to the browser.

                ``session.receive()`` in google-genai yields messages for a
                single turn and then completes. To stay alive across many
                turns we wrap it in an outer ``while not stop_event.is_set()``
                loop, re-entering ``receive()`` each time. The session
                itself stays open (the ``async with`` context manager owns
                it) until we explicitly close it or the server tears it
                down.
                """
                turn_count = 0
                try:
                    while not stop_event.is_set():
                        turn_had_data = False
                        async for response in session.receive():
                            turn_had_data = True
                            if stop_event.is_set():
                                return

                            # ── audio bytes
                            data = getattr(response, "data", None)
                            if data:
                                try:
                                    await websocket.send_bytes(data)
                                except Exception:
                                    logger.warning("voice: ws.send_bytes failed; ending")
                                    stop_event.set()
                                    return

                            server_content = getattr(response, "server_content", None)
                            if server_content is not None:
                                input_tx = getattr(server_content, "input_transcription", None)
                                if input_tx and getattr(input_tx, "text", None):
                                    try:
                                        await websocket.send_json({
                                            "type": "input_transcription",
                                            "text": input_tx.text,
                                        })
                                    except Exception:
                                        stop_event.set()
                                        return
                                output_tx = getattr(server_content, "output_transcription", None)
                                if output_tx and getattr(output_tx, "text", None):
                                    try:
                                        await websocket.send_json({
                                            "type": "output_transcription",
                                            "text": output_tx.text,
                                        })
                                    except Exception:
                                        stop_event.set()
                                        return
                                if getattr(server_content, "turn_complete", False):
                                    turn_count += 1
                                    logger.info("voice: turn_complete (#%d)", turn_count)
                                    try:
                                        await websocket.send_json({"type": "turn_complete"})
                                    except Exception:
                                        stop_event.set()
                                        return
                                if getattr(server_content, "interrupted", False):
                                    logger.info("voice: interrupted")

                            # ── server-initiated session shutdown
                            go_away = getattr(response, "go_away", None)
                            if go_away is not None:
                                time_left = getattr(go_away, "time_left", None)
                                logger.warning(
                                    "voice: server GoAway (time_left=%s) — session ending",
                                    time_left,
                                )
                                try:
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": "Voice session ending. Please restart voice mode.",
                                    })
                                except Exception:
                                    pass
                                stop_event.set()
                                return

                            resumption = getattr(response, "session_resumption_update", None)
                            if resumption is not None and getattr(resumption, "resumable", False):
                                logger.info("voice: session resumable handle received")

                            # ── tool calls
                            tool_call = getattr(response, "tool_call", None)
                            if tool_call is not None:
                                calls = list(getattr(tool_call, "function_calls", []) or [])
                                logger.info("voice: tool_call (%d functions)", len(calls))
                                responses = []
                                for call in calls:
                                    tool_name = getattr(call, "name", "tool")
                                    logger.info(
                                        "voice: tool=%s args=%s",
                                        tool_name,
                                        dict(getattr(call, "args", {}) or {}),
                                    )
                                    try:
                                        await websocket.send_json({
                                            "type": "tool_start",
                                            "tool_name": tool_name,
                                        })
                                    except Exception:
                                        stop_event.set()
                                        return
                                    with set_request_context(
                                        user_id=user["id"],
                                        natal_chart=natal_chart,
                                        chart_format=chart_format,
                                        residence=residence_payload,
                                        self_birth=self_birth_payload,
                                    ):
                                        res = await _execute_tool_call(call)
                                    if res["name"] == "render_chart_svg":
                                        if isinstance(res["result"], str) and res["result"].strip():
                                            try:
                                                await websocket.send_json({
                                                    "type": "chart_svg",
                                                    "svg": res["result"],
                                                })
                                            except Exception:
                                                stop_event.set()
                                                return
                                        # ALSO send the birth_chart card so the
                                        # seeker sees the planet table next to
                                        # the visual chart in voice mode.
                                        if natal_chart:
                                            try:
                                                await websocket.send_json({
                                                    "type": "structured_card",
                                                    "card_type": "birth_chart",
                                                    "data": natal_chart,
                                                })
                                            except Exception:
                                                stop_event.set()
                                                return
                                        res["result"] = "Chart rendered for the seeker."
                                    else:
                                        card = _maybe_card_payload(res["name"], res["result"])
                                        if card is not None:
                                            try:
                                                await websocket.send_json(card)
                                            except Exception:
                                                stop_event.set()
                                                return
                                    try:
                                        await websocket.send_json({
                                            "type": "tool_end",
                                            "tool_name": tool_name,
                                            "ok": res["ok"],
                                        })
                                    except Exception:
                                        stop_event.set()
                                        return
                                    responses.append({
                                        "id": res["id"],
                                        "name": res["name"],
                                        "response": {"result": res["result"]},
                                    })
                                if responses:
                                    try:
                                        await session.send_tool_response(function_responses=responses)
                                    except Exception:
                                        logger.exception("voice: send_tool_response failed")
                                        stop_event.set()
                                        return

                        # Inner ``async for`` ended — that's a normal end
                        # of one Live turn. If the loop produced nothing
                        # at all, the session is genuinely closed.
                        if not turn_had_data:
                            logger.warning(
                                "voice: receive() yielded nothing; treating as session close"
                            )
                            try:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Voice session ended. Please restart voice mode.",
                                })
                            except Exception:
                                pass
                            stop_event.set()
                            return
                        # Otherwise loop back into ``session.receive()`` for
                        # the next turn. ``await asyncio.sleep(0)`` yields
                        # control briefly so the browser_to_model task can
                        # interleave its mic chunks.
                        await asyncio.sleep(0)
                except Exception:
                    logger.exception("voice: model_to_browser errored")
                    stop_event.set()

            t1 = asyncio.create_task(browser_to_model())
            t2 = asyncio.create_task(model_to_browser())

            done, pending = await asyncio.wait(
                {t1, t2}, return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()
            for d in done:
                exc = d.exception()
                if exc:
                    logger.warning("voice: task ended with exception: %s", exc)

    except Exception as exc:
        logger.exception("voice: live session error: %s", exc)
        try:
            await websocket.send_json({"type": "error", "message": f"voice session error: {exc}"})
        except Exception:
            pass
    finally:
        logger.info("voice: closing ws for user=%s", user.get("email", user["id"]))
        try:
            await websocket.close()
        except Exception:
            pass
