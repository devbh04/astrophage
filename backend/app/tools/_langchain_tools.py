"""
LangChain ``@tool`` wrappers around the resolver-aware callables in
``_resolvers.py``.

The reasoning node binds these to the Gemini LLM so it can invoke them.
Both the registry (used by the executor) and these LangChain wrappers
delegate to the same ``*_resolved`` functions, so default-injection
(user's ``natal_chart``, ``chart_format``) happens identically no matter
who calls the tool.
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.tools import _resolvers as R


@tool
async def geocode_place(place_name: str) -> dict:
    """Convert a place name to lat/lng/timezone. Always run this first when the user gives a city, before any other tool that needs coordinates."""
    return await R.geocode_place_resolved(place_name)


@tool
def compute_birth_chart(
    birth_date: str,
    birth_time: str | None,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """Compute a full Vedic (sidereal Lahiri) birth chart from birth details. Returns sun_sign, moon_sign, ascendant, planets[], house_cusps."""
    return R.compute_birth_chart_resolved(birth_date, birth_time, lat, lng, timezone)


@tool
def compute_dasha_periods(
    natal_chart: dict | None = None,
    birth_date: str | None = None,
    birth_time: str | None = None,
    timezone: str | None = None,
    levels: int = 2,
    subject: str | None = None,
) -> dict:
    """Calculate the Vimshottari Dasha timeline. ``natal_chart`` may be omitted — by default the user's own preloaded chart is used. To compute a saved family member's dasha (mother, spouse, child, sibling, named person), pass ``subject="<relationship-or-name>"`` and the system will substitute their chart and birth details automatically. ``birth_date``, ``birth_time``, and ``timezone`` should usually come from the user-context block in the system prompt; they're auto-filled from the resolved subject when omitted."""
    return R.compute_dasha_periods_resolved(
        natal_chart=natal_chart,
        birth_date=birth_date,
        birth_time=birth_time,
        timezone=timezone,
        levels=levels,
        subject=subject,
    )


@tool
def compute_nakshatra_details(
    natal_chart: dict | None = None,
    subject: str | None = None,
) -> dict:
    """Janma Nakshatra deep analysis from the natal Moon. ``natal_chart`` may be omitted — by default the user's own chart is used. To analyse a saved family member's nakshatra, pass ``subject="<relationship-or-name>"``."""
    return R.compute_nakshatra_details_resolved(
        natal_chart=natal_chart, subject=subject
    )


@tool
def check_sade_sati(
    natal_chart: dict | None = None,
    as_of: str | None = None,
    subject: str | None = None,
) -> dict:
    """Check Sade Sati / Ashtama Shani status against the natal Moon. ``natal_chart`` may be omitted — by default the user's own chart is used. To check it for a saved family member, pass ``subject="<relationship-or-name>"``."""
    return R.check_sade_sati_resolved(
        natal_chart=natal_chart, as_of=as_of, subject=subject
    )


@tool
def get_panchang(
    date: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    timezone: str | None = None,
) -> dict:
    """Five limbs of Panchang for a date+place. All four arguments may be omitted — the system fills in today's date and the user's residence (lat/lng/timezone). Pass them only when the user explicitly names a date or a different place."""
    return R.get_panchang_resolved(date=date, lat=lat, lng=lng, timezone=timezone)


@tool
async def knowledge_lookup(query: str, top_k: int = 5) -> list:
    """Search the curated Vedic knowledge base. Use for conceptual questions ('what does Saturn signify?')."""
    return await R.knowledge_lookup_resolved(query, top_k=top_k)


@tool
async def kundali_milan(
    boy_chart: dict | str | None = None,
    girl_chart: dict | str | None = None,
) -> dict:
    """Ashtakoota 8-fold compatibility scoring + Mangal Dosha analysis. ``boy_chart`` may be omitted to use the seeker's preloaded chart. Either slot may be the FULL chart dict OR a string with the partner's name/relationship — when a string is given, the system looks them up in the family vault and uses their precomputed chart."""
    return await R.kundali_milan_resolved(boy_chart=boy_chart, girl_chart=girl_chart)


@tool
def render_chart_svg(
    natal_chart: dict | None = None,
    style: str | None = None,
    subject: str | None = None,
) -> str:
    """Render a natal chart as a visual SVG card. The SVG is sent to the UI as a separate ``chart_svg`` artifact — do NOT paste the returned string back into your reply, just acknowledge briefly. ``natal_chart`` may be omitted; by default the seeker's own chart is rendered. To render a saved family member's chart (mother, spouse, child, sibling, named person), pass ``subject="<relationship-or-name>"``. ``style`` may be omitted (user's chart_format preference used) or set explicitly to ``south_indian`` or ``north_indian``."""
    return R.render_chart_svg_resolved(
        natal_chart=natal_chart, style=style, subject=subject
    )


@tool
def compute_muhurta(
    purpose: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    timezone: str | None = None,
) -> dict:
    """Find top 3 auspicious 30-minute windows for a purpose (wedding/travel/business_start/griha_pravesh/general) in a date range. Date and place may be omitted — they default to today and the user's residence."""
    return R.compute_muhurta_resolved(
        purpose=purpose,
        start_date=start_date,
        end_date=end_date,
        lat=lat,
        lng=lng,
        timezone=timezone,
    )


@tool
def get_daily_transits(
    natal_chart: dict | None = None,
    as_of: str | None = None,
    subject: str | None = None,
) -> dict:
    """Current planetary transits relative to a natal chart. ``natal_chart`` may be omitted — by default the seeker's own chart is used. To compute transits for a saved family member, pass ``subject="<relationship-or-name>"``."""
    return R.get_daily_transits_resolved(
        natal_chart=natal_chart, as_of=as_of, subject=subject
    )


@tool
def get_current_sky(as_of: str | None = None) -> dict:
    """Generic current-sky snapshot — planets, moon phase, retrogrades, next event. No natal chart required."""
    return R.get_current_sky_resolved(as_of=as_of)


@tool
async def get_family_profile(
    relationship: str | None = None,
    name: str | None = None,
) -> dict:
    """Look up one of the user's saved family-vault profiles by relationship (e.g. "spouse", "mother", "son", "father", "sibling") OR by name. Returns ``{found, profile?}`` where profile contains birth details and a precomputed ``natal_chart`` you can pass into other tools. If multiple profiles match, returns ``{found: false, ambiguous: true, candidates}``."""
    return await R.get_family_profile_resolved(relationship=relationship, name=name)


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
    get_family_profile,
]


__all__ = ["LC_TOOLS"]
