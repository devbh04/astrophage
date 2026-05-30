"""
LangGraph graph assembly — slim, fast topology.

Old graph: language_detector → router → reasoning ⟷ tool_executor → sensitivity → editor → response
That made 4-5 LLM calls per turn (15-30s for "hi"). Editor pass also
introduced an interrupt that swallowed the reasoning output.

New graph: reasoning ⟷ tool_executor → response
- 1 LLM call when the model has a final answer
- 2 LLM calls when tools are needed (one to plan, one to read tool output)
- No interrupt, no fake editor pass
- Sensitive-topic gating still works — the response node checks for
  ``sensitive_flag`` and the chat HTTP handler honors it
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes.reasoning import reasoning_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.response import response_node


def needs_tool(state: AgentState) -> str:
    """Branch: did the reasoning node request a tool call?"""
    messages = state.get("messages", []) or []
    if not messages:
        return "no_tool"
    last = messages[-1]
    if hasattr(last, "tool_calls") and getattr(last, "tool_calls"):
        return "tool"
    return "no_tool"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("reasoning")
    graph.add_conditional_edges(
        "reasoning",
        needs_tool,
        {"tool": "tool_executor", "no_tool": "response"},
    )
    graph.add_edge("tool_executor", "reasoning")
    graph.add_edge("response", END)

    return graph.compile(checkpointer=MemorySaver())


agent_graph = build_graph()


__all__ = ["agent_graph", "build_graph", "needs_tool"]
