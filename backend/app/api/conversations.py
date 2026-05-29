"""Conversations API — chat history management."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.db.queries import (
    create_conversation,
    get_conversations_by_user,
    get_conversation_messages,
    update_conversation_title,
    delete_conversation,
)


router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class CreateConversationBody(BaseModel):
    profile_id: str | None = None
    title: str | None = None


class TitleBody(BaseModel):
    title: str


@router.get("/")
async def list_conversations(user: dict = Depends(get_current_user)):
    return await get_conversations_by_user(user["id"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def new_conversation(
    body: CreateConversationBody | None = None,
    user: dict = Depends(get_current_user),
):
    body = body or CreateConversationBody()
    return await create_conversation(
        user_id=user["id"],
        profile_id=body.profile_id,
        title=body.title,
    )


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    _user: dict = Depends(get_current_user),
):
    return await get_conversation_messages(conversation_id)


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    body: TitleBody,
    _user: dict = Depends(get_current_user),
):
    updated = await update_conversation_title(conversation_id, body.title)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return updated


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_conversation(
    conversation_id: str,
    _user: dict = Depends(get_current_user),
):
    await delete_conversation(conversation_id)
