"""Unit + property tests for the language-detector node."""

from __future__ import annotations

import asyncio

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.nodes.language_detector import (
    detect_language,
    language_detector_node,
)


SUPPORTED = {"en", "hi", "mr", "gu", "ta", "kn"}


def _state_with_message(text: str, **extras) -> dict:
    """Build an ``AgentState``-shaped dict with a single human message."""
    base = {"messages": [HumanMessage(content=text)]}
    base.update(extras)
    return base


def _run(coro):
    return asyncio.run(coro)


# ── Single-script detection ─────────────────────────────────────


def test_pure_latin_message_detects_english():
    state = _state_with_message("What is my Lagna and which Nakshatra rules me?")
    result = _run(language_detector_node(state))
    assert result == {"language": "en"}


def test_devanagari_hindi_message_detects_hi():
    # Plain Hindi sentence: "My name is Ram and I want to know my chart."
    state = _state_with_message("मेरा नाम राम है और मुझे अपनी कुंडली जाननी है।")
    result = _run(language_detector_node(state))
    assert result["language"] == "hi"


def test_devanagari_marathi_message_detects_mr():
    # Plain Marathi sentence: "My name is Ram and I want to see my chart."
    state = _state_with_message(
        "माझे नाव राम आहे आणि मला माझी कुंडली पाहायची आहे."
    )
    result = _run(language_detector_node(state))
    assert result["language"] == "mr"


def test_gujarati_message_detects_gu():
    # Gujarati: "My name is Ram and I want my chart."
    state = _state_with_message("મારું નામ રામ છે અને મારે મારી કુંડળી જોઈએ છે.")
    result = _run(language_detector_node(state))
    assert result["language"] == "gu"


def test_tamil_message_detects_ta():
    # Tamil: "My name is Raman and I want my chart."
    state = _state_with_message("என் பெயர் ராமன் எனக்கு என் ஜாதகம் வேண்டும்.")
    result = _run(language_detector_node(state))
    assert result["language"] == "ta"


def test_kannada_message_detects_kn():
    # Kannada: "My name is Rama and I want my chart."
    state = _state_with_message("ನನ್ನ ಹೆಸರು ರಾಮ ನನಗೆ ನನ್ನ ಜಾತಕ ಬೇಕು.")
    result = _run(language_detector_node(state))
    assert result["language"] == "kn"


# ── Mixed-script behavior ───────────────────────────────────────


def test_devanagari_dominant_mixed_script_does_not_fall_through_to_en():
    """Devanagari + a sprinkle of Latin must still pick ``hi`` or ``mr``."""
    state = _state_with_message("मेरी कुंडली बताओ please")
    result = _run(language_detector_node(state))
    assert result["language"] in {"hi", "mr"}
    assert result["language"] != "en"


def test_latin_dominant_mixed_script_picks_devanagari_when_present():
    """Even a single Devanagari word forces non-English routing.

    The design's strategy is ``any non-Latin Indic script wins over Latin``.
    """
    state = _state_with_message("My name is राम and I want my chart.")
    result = _run(language_detector_node(state))
    assert result["language"] in {"hi", "mr"}


def test_gujarati_with_english_words_still_detects_gu():
    state = _state_with_message("મારી birth chart please")
    result = _run(language_detector_node(state))
    assert result["language"] == "gu"


# ── Hindi vs. Marathi disambiguation ────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        # Hindi-only function words.
        ("मुझे अपनी कुंडली के बारे में जानना है।", "hi"),
        ("क्या आप मुझे बता सकते हैं कि मेरा भविष्य कैसा होगा?", "hi"),
        # Marathi-only function words ("आहे", "मला", "तुम्ही").
        ("मला माझ्या कुंडलीबद्दल माहिती हवी आहे.", "mr"),
        ("तुम्ही कोण आहात आणि तुमचे नाव काय आहे?", "mr"),
    ],
)
def test_devanagari_disambiguation_hi_vs_mr(text, expected):
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] == expected


# ── Fallback to user.default_language ───────────────────────────


def test_empty_message_falls_back_to_user_default_language():
    state = _state_with_message("", user={"default_language": "mr"})
    result = _run(language_detector_node(state))
    assert result["language"] == "mr"


def test_whitespace_only_message_falls_back_to_user_default():
    state = _state_with_message("   \n\t  ", user={"default_language": "ta"})
    result = _run(language_detector_node(state))
    assert result["language"] == "ta"


def test_no_messages_at_all_falls_back_to_default():
    state = {"messages": [], "user": {"default_language": "kn"}}
    result = _run(language_detector_node(state))
    assert result["language"] == "kn"


def test_no_user_defaults_to_en():
    state = _state_with_message("")
    result = _run(language_detector_node(state))
    assert result["language"] == "en"


def test_unsupported_script_only_falls_back_to_default():
    """Pure Cyrillic input has no supported-script signal — fall back."""
    state = _state_with_message("Привет мир", user={"default_language": "hi"})
    result = _run(language_detector_node(state))
    # Must land in the fallback (langdetect won't return any of our codes
    # for Cyrillic).
    assert result["language"] == "hi"


def test_only_punctuation_falls_back():
    state = _state_with_message("!!! ??? ...", user={"default_language": "gu"})
    result = _run(language_detector_node(state))
    assert result["language"] == "gu"


# ── Latest message wins (older AI/system messages ignored) ──────


def test_picks_latest_human_message_when_history_is_mixed():
    state = {
        "messages": [
            HumanMessage(content="What is my Lagna?"),
            AIMessage(content="Your Lagna is Aries."),
            HumanMessage(content="मेरी कुंडली बताओ"),
        ]
    }
    result = _run(language_detector_node(state))
    assert result["language"] in {"hi", "mr"}


# ── Direct helper coverage ──────────────────────────────────────


def test_detect_language_helper_supported_codes_only():
    assert detect_language("Hello world") == "en"
    assert detect_language("मेरा नाम राम है") in {"hi", "mr"}
    assert detect_language("મારું નામ રામ છે") == "gu"
    assert detect_language("என் பெயர் ராமன்") == "ta"
    assert detect_language("ನನ್ನ ಹೆಸರು ರಾಮ") == "kn"


# ── Property test (Property 10) ─────────────────────────────────
#
# Validates: Requirements 10.1, 10.2, 10.3
#
# For any non-empty text composed entirely of code-points from a single
# supported script's range, ``state.language`` lands in the supported set,
# AND any text containing Devanagari code-points never returns ``en``.

# Use Hypothesis text strategies anchored to each script's code-point range.
# Each generator builds a multi-character string so langdetect has signal to
# work with for the Devanagari hi/mr disambiguation case.
_devanagari_alphabet = st.characters(min_codepoint=0x0900, max_codepoint=0x097F)
_gujarati_alphabet = st.characters(min_codepoint=0x0A80, max_codepoint=0x0AFF)
_tamil_alphabet = st.characters(min_codepoint=0x0B80, max_codepoint=0x0BFF)
_kannada_alphabet = st.characters(min_codepoint=0x0C80, max_codepoint=0x0CFF)
# Latin: A-Z, a-z, plus ASCII spaces so words can form for langdetect.
_latin_alphabet = st.characters(
    whitelist_categories=(),
    whitelist_characters="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ",
)


@given(text=st.text(alphabet=_devanagari_alphabet, min_size=4, max_size=80))
@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
def test_property_devanagari_input_never_returns_english(text):
    """Validates: Requirements 10.1, 10.2"""
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] in SUPPORTED
    assert result["language"] != "en"
    # Devanagari maps specifically to hi or mr.
    assert result["language"] in {"hi", "mr"}


@given(text=st.text(alphabet=_gujarati_alphabet, min_size=4, max_size=80))
@settings(max_examples=30, deadline=None)
def test_property_gujarati_input_lands_in_gu(text):
    """Validates: Requirements 10.1"""
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] in SUPPORTED
    assert result["language"] == "gu"


@given(text=st.text(alphabet=_tamil_alphabet, min_size=4, max_size=80))
@settings(max_examples=30, deadline=None)
def test_property_tamil_input_lands_in_ta(text):
    """Validates: Requirements 10.1"""
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] in SUPPORTED
    assert result["language"] == "ta"


@given(text=st.text(alphabet=_kannada_alphabet, min_size=4, max_size=80))
@settings(max_examples=30, deadline=None)
def test_property_kannada_input_lands_in_kn(text):
    """Validates: Requirements 10.1"""
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] in SUPPORTED
    assert result["language"] == "kn"


@given(text=st.text(alphabet=_latin_alphabet, min_size=4, max_size=80))
@settings(max_examples=30, deadline=None)
def test_property_latin_input_lands_in_en(text):
    """Validates: Requirements 10.1"""
    # Skip degenerate strings that are whitespace-only after filtering.
    if not text.strip():
        return
    state = _state_with_message(text)
    result = _run(language_detector_node(state))
    assert result["language"] in SUPPORTED
    assert result["language"] == "en"
