"""Tool 3: geocode_place() — Geocode place names in any supported language."""

import httpx
from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "Astrophage/1.0 (astrology app)"}


async def geocode_place(place_name: str) -> dict:
    """
    Geocode a place name into lat/lng/timezone.

    Accepts place names in any of the 6 supported languages/scripts
    (English, Hindi, Marathi, Gujarati, Tamil, Kannada).

    Uses OpenStreetMap Nominatim (free, no API key required).

    Returns:
        {
            "lat": float,
            "lng": float,
            "timezone": str,        # e.g. "Asia/Kolkata"
            "canonical_name": str,   # display name from Nominatim
        }

    Raises:
        ValueError: If the place cannot be geocoded.
    """
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
        "accept-language": "en",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            NOMINATIM_URL, params=params, headers=HEADERS
        )
        response.raise_for_status()
        results = response.json()

    if not results:
        raise ValueError(
            f"Could not geocode place: '{place_name}'. "
            "Please provide a more specific location name."
        )

    place = results[0]
    lat = float(place["lat"])
    lng = float(place["lon"])

    # Derive timezone from coordinates
    tz = _tf.timezone_at(lat=lat, lng=lng)
    if not tz:
        tz = "UTC"

    return {
        "lat": lat,
        "lng": lng,
        "timezone": tz,
        "canonical_name": place.get("display_name", place_name),
    }
