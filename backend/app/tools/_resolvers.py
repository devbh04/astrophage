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
    get_current_natal_chart,
    get_current_residence,
    get_current_self_birth,
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
    return _compute_birth_chart(birth_date, birth_time, lat, lng, timezone)


def compute_dasha_periods_resolved(
    natal_chart: dict | None = None,
    birth_date: str | None = None,
    birth_time: str | None = None,
    timezone: str | None = None,
    levels: int = 2,
) -> dict:
    self_birth = get_current_self_birth() or {}
    return _compute_dasha_periods(
        resolve_chart(natal_chart),
        birth_date or self_birth.get("birth_date") or "",
        birth_time if birth_time is not None else self_birth.get("birth_time"),
        timezone or self_birth.get("timezone") or "Asia/Kolkata",
        levels=levels,
    )


def compute_nakshatra_details_resolved(natal_chart: dict | None = None) -> dict:
    return _compute_nakshatra_details(resolve_chart(natal_chart))


def check_sade_sati_resolved(
    natal_chart: dict | None = None,
    as_of: str | None = None,
) -> dict:
    return _check_sade_sati(resolve_chart(natal_chart), as_of=as_of)


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


def kundali_milan_resolved(
    boy_chart: dict | None = None,
    girl_chart: dict | None = None,
) -> dict:
    return _kundali_milan(resolve_chart(boy_chart), girl_chart or {})


def render_chart_svg_resolved(
    natal_chart: dict | None = None,
    style: str | None = None,
) -> str:
    return _render_chart_svg(resolve_chart(natal_chart), resolve_style(style))


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
) -> dict:
    return _get_daily_transits(resolve_chart(natal_chart), as_of=as_of)


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
