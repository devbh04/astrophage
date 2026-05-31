"""
ContextVar-based binding between the active HTTP request and any tools the
agent may call inside it.

Why: LangChain tool functions don't get the request's ``user_id`` as an
argument — the LLM never sees user identifiers. We still need
``get_family_profile`` (and any future user-scoped tool) to look up rows
that belong to *only* the user who's chatting. A ``ContextVar`` lets us
stash the id in the request handler and read it from anywhere downstream
without threading it through dozens of layers.

We also stash the user's preloaded ``natal_chart`` and ``chart_format`` so
chart-consuming tools can fall back to them when the LLM passes a partial
or empty ``natal_chart`` arg (which it does, because the system prompt
only shows a 3-line summary, not the full chart).
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_current_user_id: ContextVar[str | None] = ContextVar(
    "astrophage_user_id", default=None
)
_current_natal_chart: ContextVar[dict | None] = ContextVar(
    "astrophage_natal_chart", default=None
)
_current_chart_format: ContextVar[str] = ContextVar(
    "astrophage_chart_format", default="south_indian"
)
_current_residence: ContextVar[dict | None] = ContextVar(
    "astrophage_residence", default=None
)
_current_self_birth: ContextVar[dict | None] = ContextVar(
    "astrophage_self_birth", default=None
)
# Per-request scratch slot for the most recent ad-hoc chart the model
# computed in this turn (e.g. a partner whose details the user dictated
# inline but who isn't in the family vault yet). ``kundali_milan`` falls
# back to this when its ``girl_chart`` argument doesn't resolve to a
# saved profile.
_last_computed_chart: ContextVar[dict | None] = ContextVar(
    "astrophage_last_computed_chart", default=None
)


def get_current_user_id() -> str | None:
    return _current_user_id.get()


def get_current_natal_chart() -> dict | None:
    return _current_natal_chart.get()


def get_current_chart_format() -> str:
    return _current_chart_format.get()


def get_current_residence() -> dict | None:
    return _current_residence.get()


def get_current_self_birth() -> dict | None:
    return _current_self_birth.get()


def get_last_computed_chart() -> dict | None:
    return _last_computed_chart.get()


def set_last_computed_chart(chart: dict | None) -> None:
    """
    Update the per-request scratch chart slot.

    Called from inside the ``compute_birth_chart`` resolver so that any
    later tool in the same turn (most importantly ``kundali_milan``) can
    pick the chart up by name-fallback. Safe to call repeatedly; only
    the most recent successful computation is retained.
    """
    if isinstance(chart, dict) and chart.get("planets"):
        _last_computed_chart.set(chart)


@contextmanager
def set_current_user_id(user_id: str | None) -> Iterator[None]:
    """Bind the active user for the duration of the ``with`` block."""
    token = _current_user_id.set(user_id)
    try:
        yield
    finally:
        _current_user_id.reset(token)


@contextmanager
def set_request_context(
    *,
    user_id: str | None,
    natal_chart: dict | None = None,
    chart_format: str = "south_indian",
    residence: dict | None = None,
    self_birth: dict | None = None,
) -> Iterator[None]:
    """Bind everything tools may need from the request, atomically."""
    t1 = _current_user_id.set(user_id)
    t2 = _current_natal_chart.set(natal_chart or None)
    t3 = _current_chart_format.set(chart_format or "south_indian")
    t4 = _current_residence.set(residence or None)
    t5 = _current_self_birth.set(self_birth or None)
    try:
        yield
    finally:
        _current_self_birth.reset(t5)
        _current_residence.reset(t4)
        _current_chart_format.reset(t3)
        _current_natal_chart.reset(t2)
        _current_user_id.reset(t1)


__all__ = [
    "get_current_user_id",
    "get_current_natal_chart",
    "get_current_chart_format",
    "get_current_residence",
    "get_current_self_birth",
    "get_last_computed_chart",
    "set_current_user_id",
    "set_last_computed_chart",
    "set_request_context",
]
