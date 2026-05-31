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
from app.agent._user_context import get_current_natal_chart
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
            # Also emit a birth_chart structured card so the user always
            # sees the planet table next to the visual chart in text mode.
            chart = get_current_natal_chart()
            if isinstance(chart, dict) and chart.get("planets"):
                await adispatch_custom_event(
                    "structured_card",
                    {"card_type": "birth_chart", "data": chart},
                )
            return
        card_type = CARD_TYPES.get(tool_name)
        if not card_type:
            return
        # `data` must be a dict for the ChatCard schema. knowledge_lookup
        # returns a list, so wrap it in {hits: [...]}.
        if isinstance(result, list):
            payload: dict = {"hits": result}
        elif isinstance(result, dict):
            payload = result
        else:
            payload = {"value": result}
        await adispatch_custom_event(
            "structured_card",
            {"card_type": card_type, "data": payload},
        )
    except Exception:
        pass


async def _emit_tool_event(kind: str, tool_name: str, args=None, ok: bool = True):
    """Publish ``tool_run_start`` / ``tool_run_end`` so chat.py can collect them."""
    if adispatch_custom_event is None:
        return
    try:
        await adispatch_custom_event(
            f"tool_run_{kind}",
            {"tool": tool_name, "args": args, "ok": ok},
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
        await _emit_tool_event("start", name, args=args)

        if name not in TOOL_REGISTRY:
            err = f"Unknown tool: {name}"
            logger.warning(err)
            tool_outputs.append({"tool": name, "args": args, "result": err, "success": False})
            new_messages.append(ToolMessage(content=err, tool_call_id=call_id, name=name))
            await _emit_tool_event("end", name, args=args, ok=False)
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
                # Important: substitute a short ack for the LLM-facing tool
                # message. If the SVG XML is fed back into the next reasoning
                # turn, the LLM will paste it into its prose reply and the
                # user will see raw ``<svg>`` markup in the chat bubble.
                tool_message_content: Any = (
                    "Chart rendered and shown to the user as a visual card. "
                    "Do not paste the SVG. Just acknowledge briefly."
                )
            else:
                tool_message_content = result
            new_messages.append(
                ToolMessage(
                    content=_serialize_for_tool_message(tool_message_content),
                    tool_call_id=call_id,
                    name=name,
                )
            )
            await _emit_tool_event("end", name, args=args, ok=True)
        except Exception as exc:
            logger.exception("tool %s failed", name)
            tool_outputs.append({"tool": name, "args": args, "result": str(exc), "success": False})
            new_messages.append(
                ToolMessage(content=f"Error: {exc}", tool_call_id=call_id, name=name)
            )
            await _emit_tool_event("end", name, args=args, ok=False)

    update: dict = {
        "tool_outputs": tool_outputs,
        "messages": new_messages,
    }
    if chart_svg_to_set is not None:
        update["chart_svg"] = chart_svg_to_set
    return update
