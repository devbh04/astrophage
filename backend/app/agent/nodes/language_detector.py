"""
Language detector node — Unicode-script + langdetect based detector.

Sets `state.language` to one of `{en, hi, mr, gu, ta, kn}`.
"""

from __future__ import annotations

from app.agent.state import AgentState

# Try to seed langdetect for stability.
try:
    import langdetect  # type: ignore
    from langdetect import DetectorFactory  # type: ignore

    DetectorFactory.seed = 0
    _HAS_LANGDETECT = True
except Exception:  # pragma: no cover
    langdetect = None  # type: ignore
    _HAS_LANGDETECT = False


SCRIPT_RANGES: dict[str, tuple[int, int, str]] = {
    # name → (start, end_inclusive, default_lang)
    "Devanagari": (0x0900, 0x097F, "hi"),
    "Gujarati":   (0x0A80, 0x0AFF, "gu"),
    "Tamil":      (0x0B80, 0x0BFF, "ta"),
    "Kannada":    (0x0C80, 0x0CFF, "kn"),
}


def _detect_script(text: str) -> str | None:
    """Return the dominant non-Latin script name (or None for Latin / mixed)."""
    counts = {name: 0 for name in SCRIPT_RANGES}
    latin = 0
    for ch in text:
        cp = ord(ch)
        matched = False
        for name, (lo, hi, _) in SCRIPT_RANGES.items():
            if lo <= cp <= hi:
                counts[name] += 1
                matched = True
                break
        if not matched and ch.isalpha():
            if 0x0041 <= cp <= 0x024F:
                latin += 1
    # Pick the script with the highest count if any non-Latin is present.
    best = max(counts.items(), key=lambda item: item[1])
    if best[1] > 0:
        return best[0]
    if latin > 0:
        return "Latin"
    return None


def _disambiguate_devanagari(text: str) -> str:
    """Use langdetect to choose between hi/mr; default to hi on failure."""
    if not _HAS_LANGDETECT:
        return "hi"
    try:
        from langdetect import detect_langs  # type: ignore

        candidates = detect_langs(text)
        for lang_prob in candidates:
            code = str(lang_prob.lang)
            if code in ("hi", "mr"):
                return code
    except Exception:
        pass
    return "hi"


def detect_language(text: str, default_language: str = "en") -> str:
    """Pure helper used by both the node and tests."""
    if not text or not text.strip():
        return default_language
    script = _detect_script(text)
    if script == "Latin":
        return "en"
    if script == "Devanagari":
        lang = _disambiguate_devanagari(text)
        # Devanagari must never return "en"
        if lang == "en":
            return "hi"
        return lang
    if script == "Gujarati":
        return "gu"
    if script == "Tamil":
        return "ta"
    if script == "Kannada":
        return "kn"
    # Fallback
    return default_language or "en"


async def language_detector_node(state: AgentState) -> dict:
    """Run language detection on the latest human message."""
    last_message = ""
    for msg in reversed(state.get("messages", []) or []):
        if hasattr(msg, "type") and msg.type == "human":
            last_message = msg.content
            break
        if isinstance(msg, dict) and msg.get("role") == "user":
            last_message = msg.get("content", "")
            break

    default = state.get("language") or "en"
    lang = detect_language(last_message, default_language=default)
    return {"language": lang}


__all__ = ["language_detector_node", "detect_language"]
