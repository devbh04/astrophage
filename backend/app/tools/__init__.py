"""
Tool package — central registry of every tool the agent can call.

The reasoning node and tool executor look up tools by name in
``TOOL_REGISTRY`` and invoke them with keyword arguments matching the
function signatures documented in ``backend/app/tools/<tool>.py``.

Every entry is the resolver-aware wrapper from ``_resolvers.py`` so the
user's preloaded ``natal_chart`` and ``chart_format`` are filled in when
the LLM calls a tool with empty args.
"""

from app.tools._resolvers import (
    geocode_place_resolved,
    compute_birth_chart_resolved,
    compute_dasha_periods_resolved,
    compute_nakshatra_details_resolved,
    check_sade_sati_resolved,
    get_panchang_resolved,
    knowledge_lookup_resolved,
    kundali_milan_resolved,
    render_chart_svg_resolved,
    compute_muhurta_resolved,
    get_daily_transits_resolved,
    get_current_sky_resolved,
    get_family_profile_resolved,
)


TOOL_REGISTRY: dict = {
    # Phase 1
    "compute_birth_chart": compute_birth_chart_resolved,
    "geocode_place": geocode_place_resolved,
    # Phase 2
    "compute_dasha_periods": compute_dasha_periods_resolved,
    "compute_nakshatra_details": compute_nakshatra_details_resolved,
    "check_sade_sati": check_sade_sati_resolved,
    "get_panchang": get_panchang_resolved,
    "knowledge_lookup": knowledge_lookup_resolved,
    # Phase 3
    "kundali_milan": kundali_milan_resolved,
    "render_chart_svg": render_chart_svg_resolved,
    "compute_muhurta": compute_muhurta_resolved,
    "get_daily_transits": get_daily_transits_resolved,
    "get_current_sky": get_current_sky_resolved,
    # Phase 4 — user/family aware
    "get_family_profile": get_family_profile_resolved,
}


__all__ = ["TOOL_REGISTRY"]
