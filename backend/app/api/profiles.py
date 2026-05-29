"""Family vault API — CRUD for birth profiles + chart computation."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.db.models import BirthDetailsInput
from app.db.queries import (
    create_profile,
    get_profiles_by_user,
    get_profile_by_id,
    delete_profile,
    update_profile,
    update_profile_chart,
)
from app.tools.birth_chart import compute_birth_chart
from app.tools.dasha import compute_dasha_periods


router = APIRouter(prefix="/api/profiles", tags=["profiles"])


class ProfilePatch(BaseModel):
    name: str | None = None
    relationship: str | None = None
    birth_date: str | None = None
    birth_time: str | None = None
    lat: float | None = None
    lng: float | None = None
    timezone: str | None = None
    place_name: str | None = None


@router.get("/")
async def list_profiles(user: dict = Depends(get_current_user)):
    profiles = await get_profiles_by_user(user["id"])
    return profiles


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_profile(
    body: BirthDetailsInput,
    user: dict = Depends(get_current_user),
):
    """Create a profile and immediately compute its chart + dashas."""
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
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile",
        )

    # Best-effort chart precompute
    try:
        chart = compute_birth_chart(
            profile_data["birth_date"],
            profile_data["birth_time"],
            profile_data["lat"],
            profile_data["lng"],
            profile_data["timezone"],
        )
        dashas = None
        try:
            dashas = compute_dasha_periods(
                chart,
                profile_data["birth_date"],
                profile_data["birth_time"],
                profile_data["timezone"],
                levels=2,
            )
        except Exception:
            dashas = None
        updated = await update_profile_chart(profile["id"], chart, dashas)
        if updated:
            profile = updated
    except Exception:
        pass

    return profile


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
):
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.patch("/{profile_id}")
async def patch_profile(
    profile_id: str,
    body: ProfilePatch,
    user: dict = Depends(get_current_user),
):
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return profile
    updated = await update_profile(profile_id, updates)
    return updated or profile


@router.post("/{profile_id}/recompute")
async def recompute_chart(
    profile_id: str,
    user: dict = Depends(get_current_user),
):
    """Recompute chart + dashas for a profile and persist."""
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    try:
        chart = compute_birth_chart(
            profile["birth_date"],
            profile.get("birth_time"),
            profile["lat"],
            profile["lng"],
            profile["timezone"],
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    try:
        dashas = compute_dasha_periods(
            chart,
            profile["birth_date"],
            profile.get("birth_time"),
            profile["timezone"],
            levels=2,
        )
    except Exception:
        dashas = None
    updated = await update_profile_chart(profile_id, chart, dashas)
    return updated or {**profile, "computed_chart": chart, "computed_dashas": dashas}


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
):
    profile = await get_profile_by_id(profile_id)
    if not profile or profile["user_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    await delete_profile(profile_id)
