"""Panchang API — daily panchang endpoint (placeholder for Phase 2 tool)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/panchang", tags=["panchang"])


@router.get("/today")
async def today_panchang(lat: float = 19.076, lng: float = 72.8777):
    """
    Get today's Panchang summary.
    Default coordinates are Mumbai.
    Full implementation will be added in Phase 2 with the get_panchang tool.
    """
    return {
        "message": "Panchang computation will be available in Phase 2",
        "lat": lat,
        "lng": lng,
    }
