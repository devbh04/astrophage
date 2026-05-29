"""
Tool 1: compute_birth_chart() — Full Vedic birth chart via Swiss Ephemeris.

Uses pyswisseph with Lahiri ayanamsa to compute:
- All 9 Vedic planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
- Ascendant (Lagna)
- House cusps
- Nakshatras and padas for each planet
- Retrograde flags
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe

# ── Constants ───────────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

# Swiss Ephemeris planet IDs for the 7 visible planets
PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

# Rahu and Ketu are the Moon's nodes
MEAN_NODE = swe.MEAN_NODE  # Rahu (Mean North Node)


def _get_nakshatra(longitude: float) -> dict:
    """Get nakshatra, pada, and lord for a given sidereal longitude."""
    # Each nakshatra spans 13°20' = 13.3333°
    nak_span = 360 / 27  # 13.3333...
    nak_index = int(longitude / nak_span)
    nak_index = min(nak_index, 26)  # safety clamp

    # Each pada spans 3°20' = 3.3333°
    pada_span = nak_span / 4
    position_in_nak = longitude - (nak_index * nak_span)
    pada = int(position_in_nak / pada_span) + 1
    pada = min(pada, 4)  # safety clamp

    return {
        "nakshatra": NAKSHATRAS[nak_index],
        "pada": pada,
        "nakshatra_lord": NAKSHATRA_LORDS[nak_index],
    }


def _get_sign_and_house(
    sidereal_long: float, asc_sign_index: int
) -> tuple[str, int]:
    """Get sign name and house number for a sidereal longitude."""
    sign_index = int(sidereal_long / 30)
    sign_index = min(sign_index, 11)
    sign = SIGNS[sign_index]

    # House = (planet_sign - ascendant_sign) mod 12 + 1
    house = ((sign_index - asc_sign_index) % 12) + 1

    return sign, house


def compute_birth_chart(
    birth_date: str,
    birth_time: str | None,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """
    Compute a full Vedic (sidereal) birth chart.

    Args:
        birth_date: ISO format date string (YYYY-MM-DD)
        birth_time: Time string (HH:MM or HH:MM:SS), or None for sunrise chart
        lat: Latitude of birth place
        lng: Longitude of birth place
        timezone: IANA timezone string (e.g. "Asia/Kolkata")

    Returns:
        Complete chart dict with planets, houses, nakshatras.
    """
    # Set Lahiri ayanamsa (most common in Indian Vedic astrology)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Parse birth datetime in local timezone → convert to UTC
    tz = ZoneInfo(timezone)
    if birth_time:
        # Handle both HH:MM and HH:MM:SS
        time_parts = birth_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0
    else:
        # Unknown birth time — use 6:00 AM (approximate sunrise)
        hour, minute, second = 6, 0, 0

    dt_local = datetime(
        *map(int, birth_date.split("-")),
        hour, minute, second,
        tzinfo=tz,
    )
    dt_utc = dt_local.astimezone(ZoneInfo("UTC"))

    # Convert to Julian Day Number
    jd = swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600,
    )

    # ── Compute Ascendant + House Cusps ─────────────────────────
    cusps, ascmc = swe.houses_ex(
        jd, lat, lng, b"P", flags=swe.FLG_SIDEREAL
    )
    asc_longitude = ascmc[0]  # Ascendant in sidereal degrees
    asc_sign_index = int(asc_longitude / 30)
    asc_sign_index = min(asc_sign_index, 11)

    ascendant_info = {
        "degree": round(asc_longitude % 30, 4),
        "total_degree": round(asc_longitude, 4),
        "sign": SIGNS[asc_sign_index],
        **_get_nakshatra(asc_longitude),
    }

    # House cusps (12 houses)
    house_cusps = []
    for i, cusp in enumerate(cusps[:12], 1):
        sign_idx = int(cusp / 30) % 12
        house_cusps.append({
            "house": i,
            "degree": round(cusp % 30, 4),
            "sign": SIGNS[sign_idx],
        })

    # ── Compute Planets ─────────────────────────────────────────
    planets = []

    for name, planet_id in PLANET_IDS.items():
        pos, ret_flags = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        sidereal_long = pos[0]
        is_retrograde = bool(pos[3] < 0)  # negative speed = retrograde

        sign, house = _get_sign_and_house(sidereal_long, asc_sign_index)
        nak_info = _get_nakshatra(sidereal_long)

        planets.append({
            "name": name,
            "degree": round(sidereal_long % 30, 4),
            "total_degree": round(sidereal_long, 4),
            "sign": sign,
            "house": house,
            "retrograde": is_retrograde,
            **nak_info,
        })

    # ── Rahu (Mean North Node) ──────────────────────────────────
    rahu_pos, _ = swe.calc_ut(jd, MEAN_NODE, swe.FLG_SIDEREAL)
    rahu_long = rahu_pos[0]
    rahu_sign, rahu_house = _get_sign_and_house(rahu_long, asc_sign_index)

    planets.append({
        "name": "Rahu",
        "degree": round(rahu_long % 30, 4),
        "total_degree": round(rahu_long, 4),
        "sign": rahu_sign,
        "house": rahu_house,
        "retrograde": True,  # Rahu is always retrograde
        **_get_nakshatra(rahu_long),
    })

    # ── Ketu (180° from Rahu) ───────────────────────────────────
    ketu_long = (rahu_long + 180) % 360
    ketu_sign, ketu_house = _get_sign_and_house(ketu_long, asc_sign_index)

    planets.append({
        "name": "Ketu",
        "degree": round(ketu_long % 30, 4),
        "total_degree": round(ketu_long, 4),
        "sign": ketu_sign,
        "house": ketu_house,
        "retrograde": True,  # Ketu is always retrograde
        **_get_nakshatra(ketu_long),
    })

    # ── Derive key sign placements ──────────────────────────────
    sun_data = next(p for p in planets if p["name"] == "Sun")
    moon_data = next(p for p in planets if p["name"] == "Moon")

    return {
        "sun_sign": sun_data["sign"],
        "moon_sign": moon_data["sign"],
        "ascendant": ascendant_info,
        "planets": planets,
        "house_cusps": house_cusps,
        "ayanamsa": "Lahiri",
        "birth_time_known": birth_time is not None,
    }
