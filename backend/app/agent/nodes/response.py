"""
Response node — final assembly + sensitive-turn HiTL gate.

If `sensitive_flag` is true and `confirmed` is unset, this node leaves the
draft as a confirmation preview so the WebSocket handler can emit a
`confirmation_required` frame and pause for the user.
"""

from __future__ import annotations

from app.agent.state import AgentState


async def response_node(state: AgentState) -> dict:
    sensitive = bool(state.get("sensitive_flag")) and not state.get("confirmed")
    draft = state.get("draft_response", "")

    if sensitive:
        # Replace the streamed draft with a placeholder confirmation preview;
        # the WebSocket handler will emit a `confirmation_required` frame
        # instead of streaming tokens for this turn.
        preview = state.get("confirmation_preview") or (
            "This touches a sensitive area — let me know if you'd like to continue."
        )
        return {
            "draft_response": preview,
            "awaiting_confirmation": True,
        }

    if not draft:
        draft = (
            "I apologize, but I wasn't able to generate a response. "
            "Could you please rephrase your question?"
        )
    return {"draft_response": draft, "awaiting_confirmation": False}
