"""Agent state schema shared across all graph nodes."""

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class BirthDetails(TypedDict, total=False):
    """Birth details extracted from user input or loaded from DB."""
    date: str
    time: str | None
    place: str
    lat: float
    lng: float
    timezone: str


class AgentState(TypedDict, total=False):
    """
    Shared state flowing through the entire LangGraph graph.

    All nodes read from and write to this state. ``total=False`` means every
    field is optional; nodes populate the keys they own and downstream nodes
    read whatever is present.
    """
    # Message history — uses LangGraph's message accumulator
    messages: Annotated[list, add_messages]

    # User context
    user_id: str
    session_id: str
    language: str  # detected language code: en, hi, mr, gu, ta, kn

    # Astrology context (pre-loaded from DB when available)
    birth_details: BirthDetails
    natal_chart: dict       # full computed chart from birth_profiles.computed_chart
    active_dashas: dict     # from birth_profiles.computed_dashas

    # Agent reasoning
    intent: str             # classified by router: chart_request, daily_horoscope, etc.
    tool_outputs: list      # results from tool calls
    draft_response: str     # factual draft from reasoning node

    # Safety + HiTL
    sensitive_flag: bool
    sensitive_category: str          # "health" | "death" | "finance" | "relationship" | "none"
    confirmation_preview: str        # caring one-liner shown to the client before confirmation
    awaiting_confirmation: bool
    confirmed: bool                  # set by WebSocket-handler resume after the client confirms

    # Streaming hints surfaced as dedicated WebSocket frames
    chart_svg: str | None            # rendered SVG payload for `chart_svg` frame
    structured_card: dict | None     # arbitrary structured-card payload for `structured_card` frame


__all__ = ["AgentState", "BirthDetails"]
