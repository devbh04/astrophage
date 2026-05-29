"""
Tool Executor Node — dispatches tool calls and emits structured-card events.

After every tool returns, this node dispatches a custom LangGraph event so the
WebSocket layer can stream a `chart_svg` or `structured_card` frame to the
client. The card_type is keyed off the tool name so the UI can pick the right
renderer.
"""

from __future__ import annotations

import asyncio

try:
    # langchain-core 0.3+
    from langchain_core.callbacks.manager import adispatch_custom_event  # type: ignore
except Exception:  # pragma: no cover
    try:
        from langchain_core.callbacks import adispatch_custom_event  # type: ignore
    except Exception:
        adispatch_custom_event = None  # type: ignore

from app.agent.state import AgentState
from app.tools import TOOL_REGISTRY


# Map every tool to its card_type. ``render_chart_svg`` is special — it emits a
# ``chart_svg`` event with the SVG string directly, not wrapped in a card.
CARD_TYPES: dict[str, str] = {
    "compute_birth_chart": "birth_chart",
    "compute_dasha_periods": "dasha_timeline",
    "compute_nakshatra_details": "nakshatra",
    "check_sade_sati": "sade_sati",
    "get_panchang": "panchang",
    "knowledge_lookup": "knowledge",
    "kundali_milan": "kundali_milan",
    "compute_muhurta": "muhurta",
    "get_daily_transits": "daily_transits",
    "get_current_sky": "current_sky",
}


async def _emit_card(tool_name: str, result):
    """Best-effort dispatch of a structured-card event."""
    if adispatch_custom_event is None:
        return
    try:
        if tool_name == "render_chart_svg":
            if isinstance(result, str) and result.strip():
                await adispatch_custom_event("chart_svg", result)
            return
        card_type = CARD_TYPES.get(tool_name)
        if not card_type:
            return
        await adispatch_custom_event(
            "structured_card",
            {"card_type": card_type, "data": result},
        )
    except Exception:
        # Custom-event dispatch may fail outside a tracing context;
        # never break the agent because the UI lost a card.
        pass


async def tool_executor_node(state: AgentState) -> dict:
    """
    Execute the tool requested by the reasoning node.

    Parses the last AI message for tool call indicators,
    dispatches to the correct tool, emits a structured card
    when applicable, and appends the result to ``state.tool_outputs``.
    """
    messages = state.get("messages", [])
    tool_outputs = list(state.get("tool_outputs", []))

    if not messages:
        return {"tool_outputs": tool_outputs}

    last_msg = messages[-1]
    if not (hasattr(last_msg, "tool_calls") and last_msg.tool_calls):
        return {"tool_outputs": tool_outputs}

    chart_svg_to_set: str | None = None

    for tool_call in last_msg.tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})

        if tool_name not in TOOL_REGISTRY:
            tool_outputs.append({
                "tool": tool_name,
                "args": tool_args,
                "result": f"Unknown tool: {tool_name}",
                "success": False,
            })
            continue

        tool_fn = TOOL_REGISTRY[tool_name]
        try:
            if asyncio.iscoroutinefunction(tool_fn):
                result = await tool_fn(**tool_args)
            else:
                result = tool_fn(**tool_args)
            tool_outputs.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result,
                "success": True,
            })
            await _emit_card(tool_name, result)
            if tool_name == "render_chart_svg" and isinstance(result, str):
                chart_svg_to_set = result
        except Exception as e:
            tool_outputs.append({
                "tool": tool_name,
                "args": tool_args,
                "result": str(e),
                "success": False,
            })

    update: dict = {"tool_outputs": tool_outputs}
    if chart_svg_to_set is not None:
        update["chart_svg"] = chart_svg_to_set
    return update
