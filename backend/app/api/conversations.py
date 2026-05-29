"""Conversations API — chat history management."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.db.queries import (
    create_conversation,
    get_conversations_by_user,
    get_conversation_messages,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/")
async def list_conversations(user: dict = Depends(get_current_user)):
    """List all conversations for the current user, newest first."""
    return await get_conversations_by_user(user["id"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def new_conversation(
    profile_id: str | None = None,
    title: str | None = None,
    user: dict = Depends(get_current_user),
):
    """Create a new conversation."""
    return await create_conversation(
        user_id=user["id"],
        profile_id=profile_id,
        title=title,
    )


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Get messages for a conversation."""
    messages = await get_conversation_messages(conversation_id)
    return messages
