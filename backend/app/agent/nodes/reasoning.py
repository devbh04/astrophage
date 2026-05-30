"""
Reasoning Node — the LLM brain.

Binds the real LangChain tool wrappers so the model can actually invoke
them (instead of hallucinating tool calls and pretending to read results).
"""

from __future__ import annotations

import logging

from langchain_core.messages import SystemMessage, ToolMessage

from app.agent.state import AgentState
from app.agent._llm_text import llm_text
from app.agent._llm_factory import make_chat
from app.tools._langchain_tools import LC_TOOLS

logger = logging.getLogger(__name__)


_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "mr": "Marathi (Devanagari script)",
    "gu": "Gujarati (Gujarati script)",
    "ta": "Tamil (Tamil script)",
    "kn": "Kannada (Kannada script)",
}


REASONING_SYSTEM_PROMPT = """You are Astrophage, a warm and grounded Vedic astrology AI assistant.

You have a set of tools available. Whenever the user asks for anything that
needs computed data — Panchang, dashas, transits, charts, knowledge lookup,
muhurta, current sky — call the relevant tool(s) instead of guessing.
Never invent timing, dates, or planetary positions; always call the tools.

SPECIFIC TOOL GUIDANCE:
- ``geocode_place``: When the user mentions a city, town, or place name — always run this first to get lat/lng/timezone before any other tool that needs coordinates.
- ``knowledge_lookup``: For conceptual questions about Vedic astrology — "What does Saturn signify?", "Explain Rahu and Ketu", "What is Sade Sati?", "Tell me about Nakshatras", "What are the different types of Dasha?", "Explain the meaning of houses in astrology". Use this tool to search the curated knowledge base for accurate information.
- ``get_panchang``: For daily Panchang, tithi, nakshatra, yoga, karana, sunrise/sunset times for a specific date and place.
- ``compute_birth_chart``: When the user provides birth details (date, time, place) and wants their chart calculated.
- ``compute_dasha_periods``: For Vimshottari Dasha timeline from a natal chart.
- ``compute_nakshatra_details``: For deep analysis of the natal Moon's Nakshatra.
- ``check_sade_sati``: To check Sade Sati / Ashtama Shani status.
- ``kundali_milan``: For compatibility analysis between two charts.
- ``render_chart_svg``: To generate a visual chart SVG. The SVG is rendered as a CARD in the UI automatically — never paste the SVG XML into your reply. Just acknowledge in 1-2 lines that the chart is shown above. The user's preloaded chart and chart-format preference are auto-substituted, so you may call this with no arguments (or just ``style``).
- ``compute_muhurta``: To find auspicious timing windows for specific purposes.
- ``get_daily_transits``: For current planetary transits relative to a natal chart.
- ``get_current_sky``: For generic current planetary positions, moon phase, retrogrades.
- ``get_family_profile``: When the user asks about a family member by relationship (e.g., "spouse", "mother", "son") or by name. Returns that profile's birth details + computed natal chart, which you can then pass into other tools.

PLACE COORDINATES — IMPORTANT:
- For tools about the user's own *birth*-related calculations (compute_birth_chart, compute_dasha_periods, compute_nakshatra_details, check_sade_sati, render_chart_svg) use the BIRTH place coords from the user context.
- For ``get_panchang``: ALWAYS use the user's RESIDENCE coords from the user context. Even if the user names a different place ("panchang for Pune"), still pass the residence lat/lng/timezone — Panchang is observed from where the user lives, not from a referenced city. Only the date can change.
- For other *current* time/place tools (get_current_sky, get_daily_transits, compute_muhurta when no place is named) use the RESIDENCE coords too. If the user explicitly names a different place for these, call ``geocode_place`` first.

USER CONTEXT
- preferred response language: {language}
- user name: {user_name}
- now (Asia/Kolkata): {now_iso} ({weekday})
- chart format preference: {chart_format}
- user has natal chart loaded: {has_chart}
- user has dasha data loaded: {has_dashas}

{self_birth_block}{residence_block}{family_block}
You may use these as the default arguments for tools when the user doesn't
specify otherwise. The data is the user's own and is provided so you do not
need to ask for it again.

LANGUAGE RULE — STRICT:
Always reply in ``{language}`` regardless of the language the user wrote
in. If the user types in English but their preference is Hindi, answer in
Hindi. Do not translate Sanskrit/Vedic technical terms (Tithi, Nakshatra,
Sade Sati, Dasha, etc.) — keep them as-is, but the surrounding prose must
be in ``{language}``. Use the native script for Indic languages
(Devanagari for hi/mr, Gujarati for gu, Tamil for ta, Kannada for kn).

Stay warm and human. Avoid fatalism.
If you don't need a tool — small talk, greetings, follow-ups — just answer.
"""


async def reasoning_node(state: AgentState) -> dict:
    """
    Single LLM call with tools bound. The model decides whether to emit
    tool_calls or a final text answer.
    """
    base_llm = make_chat(temperature=0.4)
    # Bind tools first, then wrap with retry. RunnableRetry doesn't expose
    # bind_tools so the order matters.
    llm = base_llm.bind_tools(LC_TOOLS).with_retry(
        stop_after_attempt=2,
        wait_exponential_jitter=True,
        retry_if_exception_type=(Exception,),
    )

    has_chart = bool(state.get("natal_chart"))
    has_dashas = bool(state.get("active_dashas"))
    language_code = state.get("language", "en")
    language_name = _LANGUAGE_NAMES.get(language_code, language_code)
    language = f"{language_name} ({language_code})"
    user_name = state.get("user_name") or "Friend"
    chart_format = state.get("chart_format") or "south_indian"
    now_ist = state.get("now_ist") or {}
    self_birth = state.get("self_birth") or {}
    residence = state.get("residence") or {}
    family_summary = state.get("family_summary") or []

    if self_birth:
        self_birth_block = (
            "USER'S BIRTH DETAILS (use these whenever the user asks about themselves):\n"
            f"- birth_date: {self_birth.get('birth_date') or 'unknown'}\n"
            f"- birth_time: {self_birth.get('birth_time') or 'unknown'}\n"
            f"- birth_place: {self_birth.get('place_name') or 'unknown'}\n"
            f"- birth_lat: {self_birth.get('lat')}\n"
            f"- birth_lng: {self_birth.get('lng')}\n"
            f"- birth_timezone: {self_birth.get('timezone') or 'unknown'}\n\n"
        )
    else:
        self_birth_block = (
            "USER'S BIRTH DETAILS: not yet provided. If the user asks about "
            "their own chart, gently ask them to add their details in Settings.\n\n"
        )

    if residence:
        residence_block = (
            "USER'S CURRENT RESIDENCE (use for *today*'s panchang, transits, current sky):\n"
            f"- place: {residence.get('place_name')}\n"
            f"- lat: {residence.get('lat')}\n"
            f"- lng: {residence.get('lng')}\n"
            f"- timezone: {residence.get('timezone')}\n\n"
        )
    else:
        residence_block = (
            "USER'S CURRENT RESIDENCE: not set. Default to the IST timezone "
            "and ask only if the question genuinely depends on location.\n\n"
        )

    if family_summary:
        lines = ["FAMILY VAULT (saved profiles the user may reference):"]
        for entry in family_summary[:30]:
            lines.append(
                f"- {entry.get('name')} "
                f"(relationship: {entry.get('relationship') or 'unknown'}, "
                f"chart_ready: {entry.get('has_chart')})"
            )
        lines.append(
            "When the user asks about any of these, call ``get_family_profile`` "
            "with the relationship or name — that returns the full chart you "
            "can pass into other tools.\n"
        )
        family_block = "\n".join(lines) + "\n"
    else:
        family_block = "FAMILY VAULT: empty. The user has not added any family members yet.\n\n"

    system = REASONING_SYSTEM_PROMPT.format(
        language=language,
        user_name=user_name,
        now_iso=now_ist.get("iso", "unknown"),
        weekday=now_ist.get("weekday", ""),
        chart_format=chart_format,
        has_chart=has_chart,
        has_dashas=has_dashas,
        self_birth_block=self_birth_block,
        residence_block=residence_block,
        family_block=family_block,
    )

    natal_chart = state.get("natal_chart")
    if natal_chart:
        planets = natal_chart.get("planets") or []
        planet_lines = "\n".join(
            f"  - {p.get('name')}: {p.get('sign')}"
            f" (house {p.get('house')}, "
            f"{p.get('nakshatra') or '?'} pada {p.get('pada') or '?'}"
            f"{', R' if p.get('retrograde') else ''})"
            for p in planets
        ) or "  (planets array empty)"
        chart_summary = (
            f"\nUSER'S PRELOADED NATAL CHART (full):\n"
            f"- Sun: {natal_chart.get('sun_sign', '?')}\n"
            f"- Moon: {natal_chart.get('moon_sign', '?')}\n"
            f"- Ascendant: {natal_chart.get('ascendant', {}).get('sign', '?')}\n"
            f"- Planets:\n{planet_lines}\n"
            "When you call any tool that takes ``natal_chart``, you may pass\n"
            "an empty dict ``{}`` and the system will substitute this chart\n"
            "automatically. Do not invent planet positions or sign assignments.\n"
        )
        system += chart_summary

    messages = [SystemMessage(content=system)] + list(state.get("messages", []))

    response = await llm.ainvoke(messages)

    raw_tool_calls = list(getattr(response, "tool_calls", []) or [])
    logger.info(
        "reasoning: %d tool_calls, %d chars draft, tools=%s",
        len(raw_tool_calls),
        len(llm_text(response.content) or ""),
        [tc.get("name") for tc in raw_tool_calls],
    )

    return {
        "messages": [response],
        "draft_response": llm_text(response.content),
    }


__all__ = ["reasoning_node"]
