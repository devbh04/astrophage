"""
LangChain `@tool` wrappers around the bare Python functions in `app.tools.*`.

The reasoning node binds these to the Gemini LLM so it can actually invoke
them — versus the previous setup where tool names were only mentioned in the
system prompt as text, which meant the model would hallucinate calls and
results. Real bindings = real calls = real tool_start / tool_end events.
"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool

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


@tool
def geocode_place(place_name: str) -> dict:
    """Convert a place name to lat/lng/timezone. Always run this first when the user gives a city, before any other tool that needs coordinates."""
    return asyncio.run(_geocode_place(place_name)) if asyncio.iscoroutinefunction(_geocode_place) else _geocode_place(place_name)


@tool
def compute_birth_chart(
    birth_date: str,
    birth_time: str | None,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """Compute a full Vedic (sidereal Lahiri) birth chart from birth details. Returns sun_sign, moon_sign, ascendant, planets[], house_cusps."""
    return _compute_birth_chart(birth_date, birth_time, lat, lng, timezone)


@tool
def compute_dasha_periods(
    natal_chart: dict,
    birth_date: str,
    birth_time: str | None,
    timezone: str,
    levels: int = 2,
) -> dict:
    """Calculate the Vimshottari Dasha timeline from a natal chart's Moon. Returns balance_at_birth, timeline[], and active maha/antar."""
    return _compute_dasha_periods(natal_chart, birth_date, birth_time, timezone, levels=levels)


@tool
def compute_nakshatra_details(natal_chart: dict) -> dict:
    """Janma Nakshatra deep analysis from the natal Moon. Returns nakshatra, pada, lord, deity, gana, yoni, nadi, etc."""
    return _compute_nakshatra_details(natal_chart)


@tool
def check_sade_sati(natal_chart: dict, as_of: str | None = None) -> dict:
    """Check Sade Sati / Ashtama Shani status against the natal Moon. Returns phase, current_status, start/peak/end, history."""
    return _check_sade_sati(natal_chart, as_of=as_of)


@tool
def get_panchang(date: str, lat: float, lng: float, timezone: str) -> dict:
    """Five limbs of Panchang plus inauspicious windows for a given date+place. date is YYYY-MM-DD, timezone is IANA (e.g. Asia/Kolkata)."""
    return _get_panchang(date, lat, lng, timezone)


@tool
def knowledge_lookup(query: str, top_k: int = 5) -> list:
    """Search the curated Vedic knowledge base. Use for conceptual questions ('what does Saturn signify?')."""
    return asyncio.run(_knowledge_lookup(query, top_k=top_k))


@tool
def kundali_milan(boy_chart: dict, girl_chart: dict) -> dict:
    """Ashtakoota 8-fold compatibility scoring + Mangal Dosha analysis. Both inputs are full natal_chart dicts."""
    return _kundali_milan(boy_chart, girl_chart)


@tool
def render_chart_svg(natal_chart: dict, style: str = "south_indian") -> str:
    """Render a natal chart as inline SVG. style is 'south_indian' or 'north_indian'."""
    return _render_chart_svg(natal_chart, style)


@tool
def compute_muhurta(
    purpose: str,
    start_date: str,
    end_date: str,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """Find top 3 auspicious 30-minute windows for a purpose (wedding/travel/business_start/griha_pravesh/general) in a date range."""
    return _compute_muhurta(purpose, start_date, end_date, lat, lng, timezone)


@tool
def get_daily_transits(
    natal_chart: dict,
    as_of: str | None = None,
) -> dict:
    """Current planetary transits relative to a natal chart. Returns transits[], activated_houses, headline."""
    return _get_daily_transits(natal_chart, as_of=as_of)


@tool
def get_current_sky(as_of: str | None = None) -> dict:
    """Generic current-sky snapshot — planets, moon phase, retrogrades, next event. No natal chart required."""
    return _get_current_sky(as_of=as_of)


# Tools the LLM gets bound to.
LC_TOOLS: list[Any] = [
    geocode_place,
    compute_birth_chart,
    compute_dasha_periods,
    compute_nakshatra_details,
    check_sade_sati,
    get_panchang,
    knowledge_lookup,
    kundali_milan,
    render_chart_svg,
    compute_muhurta,
    get_daily_transits,
    get_current_sky,
]


__all__ = ["LC_TOOLS"]
