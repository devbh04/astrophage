"""
Single source of truth for tool callables that need request-scoped
defaults (the user's preloaded ``natal_chart``, ``chart_format``,
``residence`` coords, etc.).

Both ``TOOL_REGISTRY`` (used by the executor) and ``LC_TOOLS`` (bound to
the LLM) call into this module. That way the resolver logic runs no
matter who invokes the tool, and we never have a mismatch between what
the LLM sees in its tool docs and what actually runs.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.agent._user_context import (
    get_current_chart_format,
    get_current_family_rows,
    get_current_natal_chart,
    get_current_residence,
    get_current_self_birth,
    get_last_computed_chart,
    set_last_computed_chart,
)
from app.tools.birth_chart import compute_birth_chart as _compute_birth_chart
from app.tools.geocode import geocode_place as _geocode_place
from app.tools.dasha import compute_dasha_periods as _compute_dasha_periods
from app.tools.nakshatra import compute_nakshatra_details as _compute_nakshatra_details
from app.tools.sade_sati import check_sade_sati as _check_sade_sati
from app.tools.panchang import get_panchang as _get_panchang
from app.tools.knowledge_lookup import knowledge_lookup as _knowledge_lookup
from app.tools.kundali_milan import kundali_milan as _kundali_milan
from app.tools.chart_svg import render_chart_svg as _render_chart_svg
from app.tools.muhurta import compute_muhurta as _compute_muhurta
from app.tools.daily_transits import get_daily_transits as _get_daily_transits
from app.tools.current_sky import get_current_sky as _get_current_sky
from app.tools.family_profile import get_family_profile as _get_family_profile


IST = ZoneInfo("Asia/Kolkata")


def is_full_chart(chart: Any) -> bool:
    """A real chart has at least an ``ascendant`` and a non-empty ``planets`` list."""
    if not isinstance(chart, dict):
        return False
    planets = chart.get("planets")
    if not isinstance(planets, list) or not planets:
        return False
    if "ascendant" not in chart:
        return False
    return True


def resolve_chart(arg_chart: Any) -> dict:
    """Return the LLM's chart if complete, otherwise the request-bound chart."""
    if is_full_chart(arg_chart):
        return arg_chart  # type: ignore[return-value]
    bound = get_current_natal_chart()
    if is_full_chart(bound):
        return bound  # type: ignore[return-value]
    return arg_chart if isinstance(arg_chart, dict) else {}


def resolve_style(style: Any) -> str:
    """Pick a chart style: explicit arg → bound preference → south_indian."""
    if isinstance(style, str) and style in ("south_indian", "north_indian"):
        return style
    bound = get_current_chart_format()
    if bound in ("south_indian", "north_indian"):
        return bound
    return "south_indian"


# ── Subject resolution ─────────────────────────────────────────
#
# Many tools work on a "subject" — by default the seeker, but the user can
# also ask about a saved family member ("show my mother's chart",
# "compute Priya's dasha"). Rather than forcing the LLM to call
# ``get_family_profile`` first and thread the returned chart back into
# the next tool call (which it routinely skips), we let every chart
# tool accept a ``subject`` string. The resolver maps that string to a
# profile row from the request-scoped family vault and returns the
# corresponding chart + birth details.

_SELF_TOKENS = {"self", "me", "myself", "user", "i", "seeker"}


def _normalize_token(s: Any) -> str:
    return (s or "").strip().lower() if isinstance(s, str) else ""


def _self_payload() -> dict:
    """Return the seeker's bound payload as a uniform dict."""
    chart = get_current_natal_chart() or {}
    birth = get_current_self_birth() or {}
    return {
        "chart": chart,
        "birth_date": birth.get("birth_date"),
        "birth_time": birth.get("birth_time"),
        "timezone": birth.get("timezone") or "Asia/Kolkata",
        "name": birth.get("name") or "Self",
        "relationship": "self",
        "is_self": True,
    }


def _family_payload(row: dict) -> dict:
    """Normalize a family-vault row into a subject payload."""
    return {
        "chart": row.get("computed_chart") or {},
        "birth_date": row.get("birth_date"),
        "birth_time": row.get("birth_time"),
        "timezone": row.get("timezone") or "Asia/Kolkata",
        "name": row.get("name"),
        "relationship": row.get("relationship"),
        "is_self": False,
    }


def resolve_subject(subject: Any) -> dict | None:
    """
    Map a ``subject`` string (relationship, name, or "self") to a payload
    with their chart + birth details. Returns ``None`` if a subject was
    requested but couldn't be matched. Returns ``self`` payload when
    ``subject`` is empty/None.

    Match priority:
      1. self / me / myself / empty → seeker
      2. exact relationship (case-insensitive)
      3. exact name (case-insensitive)
      4. substring on name
      5. substring on relationship
    """
    token = _normalize_token(subject)
    if not token or token in _SELF_TOKENS:
        return _self_payload()

    rows = get_current_family_rows()
    if not rows:
        return None

    # 1. exact relationship
    for row in rows:
        if _normalize_token(row.get("relationship")) == token:
            return _family_payload(row)
    # 2. exact name
    for row in rows:
        if _normalize_token(row.get("name")) == token:
            return _family_payload(row)
    # 3. substring on name
    for row in rows:
        rname = _normalize_token(row.get("name"))
        if rname and (token in rname or rname in token):
            return _family_payload(row)
    # 4. substring on relationship
    for row in rows:
        rrel = _normalize_token(row.get("relationship"))
        if rrel and (token in rrel or rrel in token):
            return _family_payload(row)
    return None


def _subject_chart(subject: Any, fallback_chart: Any) -> dict:
    """Pick the chart for a tool call, honouring an explicit subject."""
    payload = resolve_subject(subject)
    if payload and isinstance(payload.get("chart"), dict) and payload["chart"].get("planets"):
        return payload["chart"]
    # subject was named but the family member has no precomputed chart;
    # fall back to whatever the LLM passed (or the seeker's chart).
    return resolve_chart(fallback_chart)


def _resolve_place(
    lat: Any,
    lng: Any,
    timezone: Any,
    *,
    prefer_birth: bool = False,
) -> tuple[float, float, str]:
    """
    Pick coordinates for a tool call.

    - If the LLM passed all three explicitly, honour them.
    - Else fall back to the bound residence (default for current-time tools).
    - Else fall back to the bound birth place (when ``prefer_birth`` or as
      a last resort).
    - Else default to Mumbai/IST.
    """
    if (
        isinstance(lat, (int, float))
        and isinstance(lng, (int, float))
        and isinstance(timezone, str)
        and timezone.strip()
    ):
        return float(lat), float(lng), timezone

    residence = get_current_residence() or {}
    birth = get_current_self_birth() or {}

    candidates: list[dict] = []
    if prefer_birth:
        candidates = [birth, residence]
    else:
        candidates = [residence, birth]

    for c in candidates:
        c_lat = c.get("lat")
        c_lng = c.get("lng")
        c_tz = c.get("timezone")
        if (
            isinstance(c_lat, (int, float))
            and isinstance(c_lng, (int, float))
            and isinstance(c_tz, str)
            and c_tz.strip()
        ):
            return float(c_lat), float(c_lng), c_tz

    return 19.076, 72.8777, "Asia/Kolkata"  # Mumbai default


# Per-request scratch slot for the chart that ``render_chart_svg``
# actually rendered, so the tool executor's companion ``birth_chart``
# card can show the matching planet table (e.g. mother's chart, not the
# seeker's). ContextVar so concurrent requests don't see each other's
# scratch state.
from contextvars import ContextVar as _ContextVar  # local import to avoid header churn
_last_rendered_chart: _ContextVar[dict | None] = _ContextVar(
    "astrophage_last_rendered_chart", default=None
)


def get_last_rendered_chart() -> dict | None:
    return _last_rendered_chart.get()


def _set_last_rendered_chart(chart: dict | None) -> None:
    if isinstance(chart, dict) and chart.get("planets"):
        _last_rendered_chart.set(chart)
    else:
        _last_rendered_chart.set(None)


def _today_iso() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


# ── Registry-callable wrappers ──────────────────────────────────
# All of these accept any subset of the original args (including none)
# and fill in resolver-derived defaults. Both the bare executor and the
# @tool wrappers call them.


async def geocode_place_resolved(place_name: str) -> dict:
    if asyncio.iscoroutinefunction(_geocode_place):
        return await _geocode_place(place_name)
    return _geocode_place(place_name)


def compute_birth_chart_resolved(
    birth_date: str,
    birth_time: str | None,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    chart = _compute_birth_chart(birth_date, birth_time, lat, lng, timezone)
    # Cache the freshly-computed chart on the request scope so a later
    # tool in the same turn (most importantly ``kundali_milan``) can pick
    # it up by name when the family-vault lookup fails. This is what
    # makes "compute Riya's chart, then check compatibility with Riya"
    # work when Riya isn't in the vault yet.
    try:
        set_last_computed_chart(chart)
    except Exception:
        pass
    return chart


def compute_dasha_periods_resolved(
    natal_chart: dict | None = None,
    birth_date: str | None = None,
    birth_time: str | None = None,
    timezone: str | None = None,
    levels: int = 2,
    subject: str | None = None,
) -> dict:
    payload = resolve_subject(subject) or {}
    self_birth = get_current_self_birth() or {}
    try:
        levels_int = int(levels) if levels is not None else 2
    except (TypeError, ValueError):
        levels_int = 2
    chart = _subject_chart(subject, natal_chart)
    return _compute_dasha_periods(
        chart,
        birth_date or payload.get("birth_date") or self_birth.get("birth_date") or "",
        (
            birth_time
            if birth_time is not None
            else payload.get("birth_time") or self_birth.get("birth_time")
        ),
        timezone or payload.get("timezone") or self_birth.get("timezone") or "Asia/Kolkata",
        levels=levels_int,
    )


def compute_nakshatra_details_resolved(
    natal_chart: dict | None = None,
    subject: str | None = None,
) -> dict:
    return _compute_nakshatra_details(_subject_chart(subject, natal_chart))


def check_sade_sati_resolved(
    natal_chart: dict | None = None,
    as_of: str | None = None,
    subject: str | None = None,
) -> dict:
    return _check_sade_sati(_subject_chart(subject, natal_chart), as_of=as_of)


def get_panchang_resolved(
    date: str | None = None,
    lat: Any = None,
    lng: Any = None,
    timezone: str | None = None,
) -> dict:
    rlat, rlng, rtz = _resolve_place(lat, lng, timezone)
    return _get_panchang(date or _today_iso(), rlat, rlng, rtz)


async def knowledge_lookup_resolved(query: str, top_k: int = 5) -> list:
    return await _knowledge_lookup(query, top_k=top_k)


async def kundali_milan_resolved(
    boy_chart: dict | str | None = None,
    girl_chart: dict | str | None = None,
) -> dict:
    """
    Compatibility scoring. Each chart slot may be:
    - a full chart dict
    - a string (name OR relationship) — looked up in the user's family vault
    - omitted (the user's preloaded chart fills the boy slot)

    The voice model in particular often passes a name as ``girl_chart``
    rather than threading the full chart dict back through itself; this
    resolver handles that gracefully so the LLM doesn't have to.
    """
    async def _resolve_slot(value: Any) -> dict:
        if isinstance(value, dict) and value:
            return value
        if isinstance(value, str) and value.strip():
            # First try the request-bound family vault (fast, sync).
            payload = resolve_subject(value)
            if payload and isinstance(payload.get("chart"), dict) and payload["chart"].get("planets"):
                return payload["chart"]
            # Then fall back to the async family lookup for substring
            # matches that ``resolve_subject`` may have missed (kept for
            # backward compatibility with edge cases).
            from app.tools.family_profile import get_family_profile as _gfp

            for kwargs in (
                {"relationship": value.strip()},
                {"name": value.strip()},
            ):
                lookup = await _gfp(**kwargs)
                if lookup.get("found") and lookup.get("profile"):
                    chart = lookup["profile"].get("natal_chart")
                    if isinstance(chart, dict) and chart.get("planets"):
                        return chart
            # Final fallback: if a chart was just computed in this turn
            # (e.g. the user dictated the partner's birth details
            # inline and the model called ``compute_birth_chart``
            # before reaching here), use it. This unblocks the
            # "compute then match" flow for partners not yet in the
            # family vault.
            recent = get_last_computed_chart()
            if isinstance(recent, dict) and recent.get("planets"):
                return recent
        return {}

    boy = await _resolve_slot(boy_chart)
    if not boy:
        boy = resolve_chart(None)  # falls back to the user's preloaded chart
    girl = await _resolve_slot(girl_chart)
    # Guard against missing/incomplete charts so the frontend can show a
    # friendly placeholder instead of crashing on undefined fields.
    if not (isinstance(boy, dict) and boy.get("planets")):
        return {"error": "Boy chart unavailable. Provide it explicitly or "
                          "ensure the seeker's chart is loaded."}
    if not (isinstance(girl, dict) and girl.get("planets")):
        return {"error": "Girl chart unavailable. Add the partner to the "
                          "family vault or provide their full birth details."}
    try:
        return _kundali_milan(boy, girl)
    except Exception as exc:
        return {"error": f"Could not compute the match: {exc}"}


def render_chart_svg_resolved(
    natal_chart: dict | None = None,
    style: str | None = None,
    subject: str | None = None,
) -> str:
    chart = _subject_chart(subject, natal_chart)
    # Stash the chart we actually rendered so the executor's companion
    # ``birth_chart`` card shows the right person's planet table (not
    # the seeker's, when the user asked about a family member).
    try:
        _set_last_rendered_chart(chart)
    except Exception:
        pass
    return _render_chart_svg(chart, resolve_style(style))


def compute_muhurta_resolved(
    purpose: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    lat: Any = None,
    lng: Any = None,
    timezone: str | None = None,
) -> dict:
    rlat, rlng, rtz = _resolve_place(lat, lng, timezone)
    today = _today_iso()
    return _compute_muhurta(
        (purpose or "general"),
        start_date or today,
        end_date or today,
        rlat,
        rlng,
        rtz,
    )


def get_daily_transits_resolved(
    natal_chart: dict | None = None,
    as_of: str | None = None,
    subject: str | None = None,
) -> dict:
    return _get_daily_transits(_subject_chart(subject, natal_chart), as_of=as_of)


def get_current_sky_resolved(as_of: str | None = None) -> dict:
    return _get_current_sky(as_of=as_of)


async def get_family_profile_resolved(
    relationship: str | None = None,
    name: str | None = None,
) -> dict:
    return await _get_family_profile(relationship=relationship, name=name)


__all__ = [
    "is_full_chart",
    "resolve_chart",
    "resolve_style",
    "resolve_subject",
    "get_last_rendered_chart",
    "geocode_place_resolved",
    "compute_birth_chart_resolved",
    "compute_dasha_periods_resolved",
    "compute_nakshatra_details_resolved",
    "check_sade_sati_resolved",
    "get_panchang_resolved",
    "knowledge_lookup_resolved",
    "kundali_milan_resolved",
    "render_chart_svg_resolved",
    "compute_muhurta_resolved",
    "get_daily_transits_resolved",
    "get_current_sky_resolved",
    "get_family_profile_resolved",
]
