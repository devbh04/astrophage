"""
Sensitivity classifier node — single low-temperature Gemini call returning
strict JSON `{sensitive, category, preview}`.

On malformed JSON we fail open (default `sensitive=false`) so the conversation
never gets stuck.
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.state import AgentState
from app.agent._llm_text import llm_text
from app.agent._llm_factory import make_chat
from app.config import get_settings


SENSITIVITY_SYSTEM_PROMPT = """You are a sensitivity classifier for a Vedic astrology AI.

Classify the user's latest message for emotional sensitivity. Return STRICT JSON
with this exact shape — no extra prose, no code fences:

{"sensitive": true|false,
 "category": "health" | "death" | "finance" | "relationship" | "none",
 "preview": "<one-line caring preamble in the user's target language>"}

Topics that are sensitive:
- Serious illness or imminent death of self or loved one
- Pregnancy loss, miscarriage, infertility distress
- Severe financial ruin, bankruptcy, debt crisis
- Divorce, breakup, abuse, mental-health crisis

Set `sensitive=false` and `category="none"` if the question is casual or factual.
The `preview` field should be a brief, warm one-liner setting up the conversation —
not the answer itself."""


_JSON_RE = re.compile(r"\{.*\}", re.S)


def parse_sensitivity_payload(raw: str) -> dict:
    """Parse a sensitivity-classifier response. Falls back to safe defaults."""
    if not raw:
        return {"sensitive": False, "category": "none", "preview": ""}
    text = raw.strip()
    # Strip code fences if any
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    m = _JSON_RE.search(text)
    if not m:
        return {"sensitive": False, "category": "none", "preview": ""}
    try:
        data = json.loads(m.group(0))
    except Exception:
        return {"sensitive": False, "category": "none", "preview": ""}
    sensitive = bool(data.get("sensitive", False))
    category = str(data.get("category", "none")).lower()
    if category not in {"health", "death", "finance", "relationship", "none"}:
        category = "none"
    preview = str(data.get("preview", ""))
    return {"sensitive": sensitive, "category": category, "preview": preview}


async def sensitivity_node(state: AgentState) -> dict:
    llm = make_chat(temperature=0.0)

    last_message = ""
    for msg in reversed(state.get("messages", []) or []):
        if hasattr(msg, "type") and msg.type == "human":
            last_message = msg.content
            break

    language = state.get("language", "en")

    prompt = (
        f"User language: {language}\n"
        f"User message: {last_message}\n\n"
        "Respond with strict JSON only."
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content=SENSITIVITY_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        payload = parse_sensitivity_payload(llm_text(getattr(response, "content", "")) or "")
    except Exception:
        payload = {"sensitive": False, "category": "none", "preview": ""}

    return {
        "sensitive_flag": payload["sensitive"],
        "sensitive_category": payload["category"],
        "confirmation_preview": payload["preview"],
    }


__all__ = ["sensitivity_node", "parse_sensitivity_payload"]
