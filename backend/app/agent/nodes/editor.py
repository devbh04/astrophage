"""
Editor node — second Gemini pass that polishes the factual draft.

The pass aims for warmth and care, cultural appropriateness, target language
fluency, and length proportional to the question.
"""

from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState
from app.agent._llm_text import llm_text
from app.agent._llm_factory import make_chat
from app.config import get_settings


EDITOR_SYSTEM_PROMPT = """You are the editor for a Vedic astrology AI.

Rewrite the draft response below for the target language and tone:
- Warm, grounded, never fatalistic
- Culturally appropriate to a Vedic / Indian context
- Match the target language exactly (the user expects {language})
- Length proportional to the question — don't pad simple answers
- Preserve every proper noun in the draft (planet names, sign names,
  nakshatra names, place names, dasha lord names, person names)

Return ONLY the polished response — no preamble, no explanation."""


async def editor_node(state: AgentState) -> dict:
    llm = make_chat(temperature=0.3)

    draft = state.get("draft_response", "")
    language = state.get("language", "en")

    if not draft.strip():
        return {"draft_response": draft}

    try:
        response = await llm.ainvoke([
            SystemMessage(content=EDITOR_SYSTEM_PROMPT.format(language=language)),
            HumanMessage(content=draft),
        ])
        polished = (llm_text(getattr(response, "content", "")) or "").strip()
        if not polished:
            polished = draft
    except Exception:
        polished = draft

    return {"draft_response": polished}


__all__ = ["editor_node"]
