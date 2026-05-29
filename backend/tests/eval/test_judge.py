"""Unit tests for ``app.eval.judge``.

The Gemini client is mocked: the LLM is replaced with an ``AsyncMock`` whose
``ainvoke`` queues up successive replies. Three behaviors are covered:

1. Valid JSON on the first attempt parses into the typed dict.
2. Malformed JSON on the first attempt triggers a single retry; if the retry
   succeeds the typed dict is returned.
3. Malformed JSON on both attempts produces the design-§E8 ``None``-score
   fallback with a descriptive ``comments`` string.

Validates: Requirements 15.1
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.eval import judge as judge_module
from app.eval.judge import judge_response


def _reply(content: str) -> MagicMock:
    """Build a fake LangChain-style message with a ``.content`` attribute."""
    msg = MagicMock()
    msg.content = content
    return msg


def _patched_llm(*replies: MagicMock):
    """Return a context-manager patch that swaps the judge's LLM constructor.

    Each call to the LLM's ``ainvoke`` returns the next queued reply.
    """
    fake_llm = MagicMock()
    fake_llm.ainvoke = AsyncMock(side_effect=list(replies))
    constructor = MagicMock(return_value=fake_llm)
    return patch.object(judge_module, "ChatGoogleGenerativeAI", constructor), fake_llm


CASE = {
    "id": "ev_test",
    "input": "Tell me about my Sun sign.",
    "judge_rubric": ["warmth", "cultural_appropriateness", "helpfulness", "fluency"],
}


@pytest.mark.asyncio
async def test_valid_json_parses_into_typed_dict():
    """First-attempt valid JSON should parse straight into ``JudgeScores``."""
    valid_json = (
        '{"warmth": 5, "cultural_appropriateness": 4, '
        '"helpfulness": 5, "fluency": 4, "comments": "warm and clear"}'
    )
    cm, fake_llm = _patched_llm(_reply(valid_json))
    with cm:
        result = await judge_response(CASE, "Your Sun is in Aries.", "en")

    assert result["warmth"] == 5
    assert result["cultural_appropriateness"] == 4
    assert result["helpfulness"] == 5
    assert result["fluency"] == 4
    assert result["comments"] == "warm and clear"
    # No retry needed when the first reply is valid.
    assert fake_llm.ainvoke.await_count == 1


@pytest.mark.asyncio
async def test_single_retry_recovers_from_malformed_first_reply():
    """Malformed JSON triggers exactly one retry; valid retry parses cleanly."""
    bad_first = "Sure! Here are the scores in plain English: warmth is 5..."
    valid_retry = (
        '{"warmth": 3, "cultural_appropriateness": 3, '
        '"helpfulness": 4, "fluency": 4, "comments": "ok"}'
    )
    cm, fake_llm = _patched_llm(_reply(bad_first), _reply(valid_retry))
    with cm:
        result = await judge_response(CASE, "Your Sun is in Aries.", "en")

    assert result["warmth"] == 3
    assert result["cultural_appropriateness"] == 3
    assert result["helpfulness"] == 4
    assert result["fluency"] == 4
    assert result["comments"] == "ok"
    # Exactly one retry — no more, no fewer.
    assert fake_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_null_fallback_after_two_malformed_replies():
    """Two malformed replies in a row produce the §E8 null-score fallback."""
    bad_first = "warmth: 5, fluency: 5"
    bad_second = "still not json"
    cm, fake_llm = _patched_llm(_reply(bad_first), _reply(bad_second))
    with cm:
        result = await judge_response(CASE, "Your Sun is in Aries.", "en")

    assert result["warmth"] is None
    assert result["cultural_appropriateness"] is None
    assert result["helpfulness"] is None
    assert result["fluency"] is None
    assert isinstance(result["comments"], str)
    assert result["comments"]  # non-empty failure description
    # Stops at exactly two attempts — no third try.
    assert fake_llm.ainvoke.await_count == 2


@pytest.mark.asyncio
async def test_fenced_json_in_first_reply_is_extracted():
    """Markdown-fenced JSON is recoverable on the first attempt without retry."""
    fenced = (
        "```json\n"
        '{"warmth": 4, "cultural_appropriateness": 5, '
        '"helpfulness": 4, "fluency": 5, "comments": "good"}\n'
        "```"
    )
    cm, fake_llm = _patched_llm(_reply(fenced))
    with cm:
        result = await judge_response(CASE, "Your Sun is in Aries.", "en")

    assert result["warmth"] == 4
    assert result["fluency"] == 5
    assert result["comments"] == "good"
    assert fake_llm.ainvoke.await_count == 1


@pytest.mark.asyncio
async def test_out_of_range_score_treated_as_malformed_then_retry_succeeds():
    """A score outside 1..5 is malformed; retry with a valid reply succeeds."""
    out_of_range = (
        '{"warmth": 7, "cultural_appropriateness": 4, '
        '"helpfulness": 5, "fluency": 4, "comments": "bad range"}'
    )
    valid_retry = (
        '{"warmth": 4, "cultural_appropriateness": 4, '
        '"helpfulness": 4, "fluency": 4, "comments": "ok"}'
    )
    cm, fake_llm = _patched_llm(_reply(out_of_range), _reply(valid_retry))
    with cm:
        result = await judge_response(CASE, "Your Sun is in Aries.", "en")

    assert result["warmth"] == 4
    assert fake_llm.ainvoke.await_count == 2
