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
- ``render_chart_svg``: To generate a visual chart SVG.
- ``compute_muhurta``: To find auspicious timing windows for specific purposes.
- ``get_daily_transits``: For current planetary transits relative to a natal chart.
- ``get_current_sky``: For generic current planetary positions, moon phase, retrogrades.

When the user references a city, call ``geocode_place`` first to get
lat/lng/timezone, then pass those into the tool that needs them.

Stay warm and human. Avoid fatalism. Match the user's language.
If you don't need a tool — small talk, greetings, follow-ups — just answer.

CONTEXT
- detected language: {language}
- user has natal chart loaded: {has_chart}
- user has dasha data loaded: {has_dashas}
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
    language = state.get("language", "en")

    system = REASONING_SYSTEM_PROMPT.format(
        language=language, has_chart=has_chart, has_dashas=has_dashas,
    )

    natal_chart = state.get("natal_chart")
    if natal_chart:
        chart_summary = (
            f"\n\nUser's preloaded natal chart:\n"
            f"- Sun: {natal_chart.get('sun_sign', '?')}\n"
            f"- Moon: {natal_chart.get('moon_sign', '?')}\n"
            f"- Ascendant: {natal_chart.get('ascendant', {}).get('sign', '?')}\n"
            "Use this chart directly when the user asks about their own chart, "
            "dasha, transits, or sade sati — pass it into tools that need it.\n"
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
