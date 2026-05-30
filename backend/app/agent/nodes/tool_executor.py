"""
Tool Executor Node — runs tool calls emitted by the reasoning LLM.

Reads ``tool_calls`` off the most recent AIMessage, dispatches each call
to the matching tool in ``TOOL_REGISTRY``, appends a ``ToolMessage`` per
call so the reasoning node's next turn can read the result, and emits
``structured_card`` / ``chart_svg`` custom events for the UI.
"""

from __future__ import annotations

import asyncio
import json
import logging

from langchain_core.messages import ToolMessage

try:
    from langchain_core.callbacks.manager import adispatch_custom_event  # type: ignore
except Exception:  # pragma: no cover
    try:
        from langchain_core.callbacks import adispatch_custom_event  # type: ignore
    except Exception:
        adispatch_custom_event = None  # type: ignore

from app.agent.state import AgentState
from app.tools import TOOL_REGISTRY


logger = logging.getLogger(__name__)


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
        pass


def _serialize_for_tool_message(value) -> str:
    """Tool messages need a string content. JSON-encode dicts/lists."""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


async def tool_executor_node(state: AgentState) -> dict:
    """Run the tools the LLM requested, append ToolMessages back to history."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last = messages[-1]
    tool_calls = list(getattr(last, "tool_calls", []) or [])
    if not tool_calls:
        return {}

    tool_outputs = list(state.get("tool_outputs", []))
    new_messages: list = []
    chart_svg_to_set: str | None = None

    for tc in tool_calls:
        # bind_tools produces dicts with keys: name, args, id
        name = tc.get("name", "")
        args = tc.get("args", {}) or {}
        call_id = tc.get("id", "")

        logger.info("tool_executor: calling %s with args=%s", name, args)

        if name not in TOOL_REGISTRY:
            err = f"Unknown tool: {name}"
            logger.warning(err)
            tool_outputs.append({"tool": name, "args": args, "result": err, "success": False})
            new_messages.append(ToolMessage(content=err, tool_call_id=call_id, name=name))
            continue

        fn = TOOL_REGISTRY[name]
        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(**args)
            else:
                result = fn(**args)
            tool_outputs.append({"tool": name, "args": args, "result": result, "success": True})
            await _emit_card(name, result)
            if name == "render_chart_svg" and isinstance(result, str):
                chart_svg_to_set = result
            new_messages.append(
                ToolMessage(
                    content=_serialize_for_tool_message(result),
                    tool_call_id=call_id,
                    name=name,
                )
            )
        except Exception as exc:
            logger.exception("tool %s failed", name)
            tool_outputs.append({"tool": name, "args": args, "result": str(exc), "success": False})
            new_messages.append(
                ToolMessage(content=f"Error: {exc}", tool_call_id=call_id, name=name)
            )

    update: dict = {
        "tool_outputs": tool_outputs,
        "messages": new_messages,
    }
    if chart_svg_to_set is not None:
        update["chart_svg"] = chart_svg_to_set
    return update
