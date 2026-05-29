"""Panchang API — daily panchang convenience endpoint."""

from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.tools.panchang import get_panchang


router = APIRouter(prefix="/api/panchang", tags=["panchang"])


@router.get("/today")
async def today_panchang(
    lat: float = 19.076,
    lng: float = 72.8777,
    timezone: str = "Asia/Kolkata",
    _user: dict = Depends(get_current_user),
):
    """Today's Panchang for the given coordinates / timezone."""
    today = date_type.today().isoformat()
    try:
        return get_panchang(today, lat, lng, timezone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/")
async def panchang_for_date(
    date: str,
    lat: float = 19.076,
    lng: float = 72.8777,
    timezone: str = "Asia/Kolkata",
    _user: dict = Depends(get_current_user),
):
    """Panchang for an arbitrary date."""
    try:
        return get_panchang(date, lat, lng, timezone)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
