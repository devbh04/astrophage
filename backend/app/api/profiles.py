"""Family vault API — CRUD for birth profiles."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.db.models import BirthDetailsInput, ProfileResponse
from app.db.queries import (
    create_profile,
    get_profiles_by_user,
    get_profile_by_id,
    delete_profile,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.get("/")
async def list_profiles(user: dict = Depends(get_current_user)):
    """List all birth profiles for the current user."""
    profiles = await get_profiles_by_user(user["id"])
    return profiles


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_profile(
    body: BirthDetailsInput,
    user: dict = Depends(get_current_user),
):
    """Add a new birth profile to the family vault."""
    profile_data = {
        "name": body.name,
        "relationship": body.relationship,
        "birth_date": body.birth_date.isoformat(),
        "birth_time": body.birth_time.isoformat() if body.birth_time else None,
        "lat": body.lat,
        "lng": body.lng,
        "timezone": body.timezone,
        "place_name": body.place_name,
    }
    profile = await create_profile(user["id"], profile_data)
    return profile


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a single birth profile."""
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a birth profile."""
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    await delete_profile(profile_id)
