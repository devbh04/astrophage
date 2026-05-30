"""
Single source of truth for tool callables that need request-scoped
defaults (the user's preloaded ``natal_chart`` and ``chart_format``).

Both ``TOOL_REGISTRY`` (used by the executor) and ``LC_TOOLS`` (bound to
the LLM) call into this module. That way the resolver logic runs no
matter who invokes the tool, and we never have a mismatch between what
the LLM sees in its tool docs and what actually runs.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agent._user_context import (
    get_current_chart_format,
    get_current_natal_chart,
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


# ── Registry-callable wrappers ──────────────────────────────────
# All of these accept any subset of the original args (including none)
# and fill in resolver-derived defaults. Both the bare executor and the
# @tool wrappers call them.


def geocode_place_resolved(place_name: str) -> dict:
    return (
        asyncio.run(_geocode_place(place_name))
        if asyncio.iscoroutinefunction(_geocode_place)
        else _geocode_place(place_name)
    )


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
    return _compute_dasha_periods(
        resolve_chart(natal_chart),
        birth_date or "",
        birth_time,
        timezone or "Asia/Kolkata",
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
    date: str,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    return _get_panchang(date, lat, lng, timezone)


def knowledge_lookup_resolved(query: str, top_k: int = 5) -> list:
    return asyncio.run(_knowledge_lookup(query, top_k=top_k))


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
    purpose: str,
    start_date: str,
    end_date: str,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    return _compute_muhurta(purpose, start_date, end_date, lat, lng, timezone)


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
