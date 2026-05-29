"""Tool Executor Node — dispatches tool calls and returns results."""

import asyncio

from app.agent.state import AgentState
from app.tools import TOOL_REGISTRY


async def tool_executor_node(state: AgentState) -> dict:
    """
    Execute the tool requested by the reasoning node.

    Parses the last AI message for tool call indicators,
    dispatches to the correct tool, and appends the result
    to state.tool_outputs.
    """
    messages = state.get("messages", [])
    tool_outputs = list(state.get("tool_outputs", []))

    if not messages:
        return {"tool_outputs": tool_outputs}

    last_msg = messages[-1]

    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        for tool_call in last_msg.tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})

            if tool_name in TOOL_REGISTRY:
                try:
                    tool_fn = TOOL_REGISTRY[tool_name]
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
                except Exception as e:
                    tool_outputs.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": str(e),
                        "success": False,
                    })
            else:
                tool_outputs.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": f"Unknown tool: {tool_name}",
                    "success": False,
                })

    return {"tool_outputs": tool_outputs}
