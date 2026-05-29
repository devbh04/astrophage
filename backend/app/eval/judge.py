"""
LLM judge for the evaluation harness.

`judge_response` calls Gemini at low temperature with a strict-JSON prompt
and returns ``{warmth, cultural_appropriateness, helpfulness, fluency, comments}``.

On a malformed response we retry once with a stricter prompt; on a second
failure we return all `null` scores plus a `comments` field describing the
failure mode (per design E8).
"""

from __future__ import annotations

import json
import re

from app.config import get_settings


JUDGE_SYSTEM_PROMPT = """You are an evaluation judge for a Vedic astrology assistant.

Score the assistant's response on the four axes below using integers 1..5.
Return STRICT JSON only — no prose, no code fences:

{"warmth": 1..5, "cultural_appropriateness": 1..5,
 "helpfulness": 1..5, "fluency": 1..5,
 "comments": "<one short sentence>"}"""


_JSON_RE = re.compile(r"\{.*\}", re.S)


def _parse_judge_payload(raw: str) -> dict | None:
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    m = _JSON_RE.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    required = {"warmth", "cultural_appropriateness", "helpfulness", "fluency"}
    if not required.issubset(data.keys()):
        return None
    return data


async def _invoke(client, system: str, user: str) -> str:
    """Tiny wrapper so callers can inject mocked clients for tests."""
    if client is None:
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        from langchain_core.messages import SystemMessage, HumanMessage  # type: ignore
        from app.agent._llm_text import llm_text  # type: ignore
        settings = get_settings()
        if settings.use_vertex:
            client = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                credentials=settings.google_credentials(),
                project=settings.gcp_project,
                location=settings.gcp_location,
                temperature=0.0,
            )
        else:
            client = ChatGoogleGenerativeAI(
                model=settings.llm_model,
                google_api_key=settings.google_api_key,
                temperature=0.0,
            )
        response = await client.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=user),
        ])
        return llm_text(getattr(response, "content", "")) or ""
    # If a custom client is supplied, expect it to be a callable
    return await client(system, user)


async def judge_response(
    case: dict,
    response: str,
    language: str,
    *,
    client=None,
) -> dict:
    """Run the judge. Always returns a dict with all five fields."""
    user_prompt = (
        f"Case id: {case.get('id')}\n"
        f"Language: {language}\n"
        f"Question: {case.get('input')}\n"
        f"Assistant response: {response}\n\n"
        "Score now. Strict JSON only."
    )

    try:
        raw = await _invoke(client, JUDGE_SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        return {
            "warmth": None, "cultural_appropriateness": None,
            "helpfulness": None, "fluency": None,
            "comments": f"judge_invoke_failed:{exc}",
        }
    parsed = _parse_judge_payload(raw)
    if parsed is not None:
        return {
            "warmth": parsed.get("warmth"),
            "cultural_appropriateness": parsed.get("cultural_appropriateness"),
            "helpfulness": parsed.get("helpfulness"),
            "fluency": parsed.get("fluency"),
            "comments": parsed.get("comments", ""),
        }

    # Retry once with a stricter prompt
    stricter = JUDGE_SYSTEM_PROMPT + "\nReply with valid JSON. Only the JSON object."
    try:
        raw2 = await _invoke(client, stricter, user_prompt)
    except Exception as exc:
        return {
            "warmth": None, "cultural_appropriateness": None,
            "helpfulness": None, "fluency": None,
            "comments": f"judge_retry_failed:{exc}",
        }
    parsed2 = _parse_judge_payload(raw2)
    if parsed2 is not None:
        return {
            "warmth": parsed2.get("warmth"),
            "cultural_appropriateness": parsed2.get("cultural_appropriateness"),
            "helpfulness": parsed2.get("helpfulness"),
            "fluency": parsed2.get("fluency"),
            "comments": parsed2.get("comments", ""),
        }
    return {
        "warmth": None, "cultural_appropriateness": None,
        "helpfulness": None, "fluency": None,
        "comments": "malformed_judge_output",
    }


__all__ = ["judge_response"]
