"""Reasoning Node — the main LLM brain that decides tool calls or drafts responses."""

from langchain_core.messages import SystemMessage

from app.agent.state import AgentState
from app.agent._llm_text import llm_text
from app.agent._llm_factory import make_chat
from app.config import get_settings


REASONING_SYSTEM_PROMPT = """You are Astrophage, a wise and compassionate Vedic astrology AI assistant.
You combine deep knowledge of Jyotish Shastra with modern AI precision.

You have access to these tools — call them via tool calls when you need data:

- compute_birth_chart(birth_date, birth_time, lat, lng, timezone)
    Compute a full Vedic birth chart from birth details.
- geocode_place(place_name)
    Convert a place name to lat/lng/timezone.
- compute_dasha_periods(natal_chart, birth_date, birth_time, timezone, levels=2)
    Calculate the Vimshottari Dasha timeline (Maha + Antar) for a natal chart.
- compute_nakshatra_details(natal_chart)
    Return Janma Nakshatra deep analysis (lord, deity, gana, yoni, nadi, etc.).
- check_sade_sati(natal_chart, as_of=None)
    Check Sade Sati / Ashtama Shani status against the natal Moon.
- get_panchang(date, lat, lng, timezone)
    Five limbs of Panchang plus Rahu Kaal / Yamaganda / Gulika / Abhijit Muhurta.
- knowledge_lookup(query, top_k=5, filters=None)
    Search the curated Vedic knowledge base for grounding passages.
- kundali_milan(boy_chart, girl_chart)
    Ashtakoota 8-fold compatibility scoring + Mangal Dosha.
- render_chart_svg(natal_chart, style="south_indian")
    Pure-Python SVG of the chart in South or North Indian style.
- compute_muhurta(purpose, start_date, end_date, lat, lng, timezone)
    Top 3 auspicious 30-minute windows for a purpose in a date range.
- get_daily_transits(natal_chart, as_of=None, lat=None, lng=None)
    Current planetary transits relative to a natal chart.
- get_current_sky(as_of=None, lat=None, lng=None)
    Generic current-sky snapshot (planets, moon phase, retrogrades, next event).

CONTEXT:
- User's detected language: {language}
- Routed intent: {intent}
- User has natal chart loaded: {has_chart}
- User has Dasha data loaded: {has_dashas}

GUIDELINES:
1. If birth details are missing for a chart-dependent question, ask politely.
2. If the natal chart is already loaded, USE it directly — do not recompute.
3. For knowledge questions, prefer `knowledge_lookup` to ground your answer.
4. Be warm and grounded. Avoid fatalism. Cite specific positions when relevant.
5. Match the user's detected language in any prose you produce.
"""


async def reasoning_node(state: AgentState) -> dict:
    llm = make_chat(temperature=0.7)

    has_chart = bool(state.get("natal_chart"))
    has_dashas = bool(state.get("active_dashas"))
    language = state.get("language", "en")
    intent = state.get("intent", "free_form")

    system = REASONING_SYSTEM_PROMPT.format(
        language=language,
        intent=intent,
        has_chart=has_chart,
        has_dashas=has_dashas,
    )

    tool_outputs = state.get("tool_outputs", [])
    if tool_outputs:
        tool_context = "\n\nPrevious tool results:\n"
        for output in tool_outputs:
            tool_context += f"- {output.get('tool', 'unknown')}: {output.get('result', '')}\n"
        system += tool_context

    natal_chart = state.get("natal_chart")
    if natal_chart:
        chart_summary = (
            f"\n\nUser's natal chart (preloaded):\n"
            f"- Sun: {natal_chart.get('sun_sign', 'unknown')}\n"
            f"- Moon: {natal_chart.get('moon_sign', 'unknown')}\n"
            f"- Ascendant: {natal_chart.get('ascendant', {}).get('sign', 'unknown')}\n"
        )
        for p in natal_chart.get("planets", []):
            chart_summary += (
                f"- {p['name']}: {p['sign']} (House {p['house']}, "
                f"{p.get('nakshatra', '?')} Pada {p.get('pada', '?')}"
                f"{', R' if p.get('retrograde') else ''})\n"
            )
        system += chart_summary

    messages = [SystemMessage(content=system)] + list(state.get("messages", []))
    response = await llm.ainvoke(messages)
    return {
        "messages": [response],
        "draft_response": llm_text(response.content),
    }
