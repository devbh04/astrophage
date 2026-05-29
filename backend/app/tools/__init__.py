"""
Tool package — central registry of every tool the agent can call.

The reasoning node and tool executor look up tools by name in
``TOOL_REGISTRY`` and invoke them with keyword arguments matching the
function signatures documented in ``backend/app/tools/<tool>.py``.
"""

from app.tools.birth_chart import compute_birth_chart
from app.tools.geocode import geocode_place
from app.tools.dasha import compute_dasha_periods
from app.tools.nakshatra import compute_nakshatra_details
from app.tools.sade_sati import check_sade_sati
from app.tools.panchang import get_panchang
from app.tools.knowledge_lookup import knowledge_lookup
from app.tools.kundali_milan import kundali_milan
from app.tools.chart_svg import render_chart_svg
from app.tools.muhurta import compute_muhurta
from app.tools.daily_transits import get_daily_transits
from app.tools.current_sky import get_current_sky


TOOL_REGISTRY: dict = {
    # Phase 1
    "compute_birth_chart": compute_birth_chart,
    "geocode_place": geocode_place,
    # Phase 2
    "compute_dasha_periods": compute_dasha_periods,
    "compute_nakshatra_details": compute_nakshatra_details,
    "check_sade_sati": check_sade_sati,
    "get_panchang": get_panchang,
    "knowledge_lookup": knowledge_lookup,
    # Phase 3
    "kundali_milan": kundali_milan,
    "render_chart_svg": render_chart_svg,
    "compute_muhurta": compute_muhurta,
    "get_daily_transits": get_daily_transits,
    "get_current_sky": get_current_sky,
}


__all__ = ["TOOL_REGISTRY"]
