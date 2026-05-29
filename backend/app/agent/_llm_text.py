"""Tiny helper to normalize LangChain message `.content` to a plain string.

Newer ``langchain-google-genai`` versions return ``response.content`` as a
list of content blocks (e.g. ``[{"type": "text", "text": "..."}]``) instead
of a flat string. Every consumer that calls ``.strip()`` or ``.startswith()``
on the content needs to coerce it first.
"""

from __future__ import annotations

from typing import Any


def llm_text(content: Any) -> str:
    """Coerce a LangChain message `content` value to a plain string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                # Most provider SDKs use either {"text": ...} or {"type":"text","text":...}
                text_val = block.get("text")
                if isinstance(text_val, str):
                    parts.append(text_val)
                else:
                    # Last-resort stringification
                    parts.append(str(block.get("content", "")))
        return "".join(parts)
    return str(content)


__all__ = ["llm_text"]
