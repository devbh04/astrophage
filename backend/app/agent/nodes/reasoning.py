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

    tool_call_count = len(getattr(response, "tool_calls", []) or [])
    logger.info(
        "reasoning: %d tool_calls, %d chars draft",
        tool_call_count,
        len(llm_text(response.content) or ""),
    )

    return {
        "messages": [response],
        "draft_response": llm_text(response.content),
    }


__all__ = ["reasoning_node"]
