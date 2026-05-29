"""
LangGraph graph assembly — Phase 4 full topology.

Graph structure:

    language_detector
        ↓
      router
        ↓
    reasoning ⟷ tool_executor
        ↓ (no_tool)
    sensitivity
        ↓
    sensitive? ── yes → response (interrupt for HiTL) ── confirm? → editor → response → END
              └ no  → editor → response → END
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes.router import router_node
from app.agent.nodes.reasoning import reasoning_node
from app.agent.nodes.tool_executor import tool_executor_node
from app.agent.nodes.response import response_node
from app.agent.nodes.language_detector import language_detector_node
from app.agent.nodes.sensitivity import sensitivity_node
from app.agent.nodes.editor import editor_node


def needs_tool(state: AgentState) -> str:
    """Branch: did the reasoning node request a tool call?"""
    messages = state.get("messages", []) or []
    if not messages:
        return "no_tool"
    last = messages[-1]
    if hasattr(last, "tool_calls") and getattr(last, "tool_calls"):
        return "tool"
    return "no_tool"


def is_sensitive(state: AgentState) -> str:
    """Branch: did the sensitivity classifier flag the message?"""
    if state.get("sensitive_flag") and not state.get("confirmed"):
        return "sensitive"
    return "safe"


def build_graph() -> StateGraph:
    """Build and compile the Phase 4 agent graph with HiTL interrupt."""
    graph = StateGraph(AgentState)

    graph.add_node("language_detector", language_detector_node)
    graph.add_node("router", router_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("sensitivity", sensitivity_node)
    graph.add_node("editor", editor_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("language_detector")
    graph.add_edge("language_detector", "router")
    graph.add_edge("router", "reasoning")
    graph.add_conditional_edges(
        "reasoning",
        needs_tool,
        {"tool": "tool_executor", "no_tool": "sensitivity"},
    )
    graph.add_edge("tool_executor", "reasoning")
    graph.add_conditional_edges(
        "sensitivity",
        is_sensitive,
        {"sensitive": "response", "safe": "editor"},
    )
    graph.add_edge("editor", "response")
    graph.add_edge("response", END)

    return graph.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["editor"],
    )


# Singleton compiled graph
agent_graph = build_graph()


__all__ = ["agent_graph", "build_graph", "needs_tool", "is_sensitive"]
