"""
Current Sky tool — generic snapshot of planetary positions at `as_of`.

Returns the nine grahas with sidereal sign/degree/retrograde/nakshatra,
the moon phase with illumination, current retrogrades, and the next
sign-change / next ephemeris event.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import swisseph as swe

from app.tools.dasha import _parse_as_of, NAK_SPAN
from app.tools.nakshatra import NAKSHATRAS

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


def _to_jd(dt: datetime) -> float:
    dt_utc = dt.astimezone(timezone.utc)
    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _planet_long(jd: float, planet_id: int) -> tuple[float, bool]:
    pos, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
    return pos[0] % 360.0, bool(pos[3] < 0)


def _nakshatra_for(longitude: float) -> str:
    idx = int(longitude // NAK_SPAN) % 27
    return NAKSHATRAS[idx]


def _illumination(jd: float) -> float:
    """Compute Moon illumination fraction in [0, 1]."""
    sun_long, _ = swe.calc_ut(jd, swe.SUN, 0)
    moon_long, _ = swe.calc_ut(jd, swe.MOON, 0)
    elong = math.radians((moon_long[0] - sun_long[0]) % 360.0)
    return (1.0 - math.cos(elong)) / 2.0


def _moon_phase_name(illum: float, waxing: bool) -> str:
    if illum < 0.04:
        return "New Moon"
    if illum > 0.96:
        return "Full Moon"
    if waxing:
        if illum < 0.5:
            return "Waxing Crescent"
        if illum < 0.96:
            return "Waxing Gibbous"
    else:
        if illum > 0.5:
            return "Waning Gibbous"
        if illum > 0.04:
            return "Waning Crescent"
    return "Quarter"


def _next_extreme_moon(jd: float, target: str) -> datetime:
    """Find next full-moon (target='full') or new-moon (target='new')."""
    cursor = jd
    last_illum = _illumination(cursor)
    for _ in range(60):  # 60 days look-ahead
        cursor += 1.0
        illum = _illumination(cursor)
        if target == "full" and illum > 0.99:
            return _jd_to_datetime(cursor)
        if target == "new" and illum < 0.02:
            return _jd_to_datetime(cursor)
        last_illum = illum
    return _jd_to_datetime(cursor)


def _jd_to_datetime(jd: float) -> datetime:
    y, m, d, frac = swe.revjul(jd)
    seconds = int(round(frac * 3600.0))
    hour, rem = divmod(seconds, 3600)
    minute, second = divmod(rem, 60)
    if hour >= 24:
        hour -= 24
        return datetime(int(y), int(m), int(d), hour, minute, second, tzinfo=timezone.utc) + timedelta(days=1)
    return datetime(int(y), int(m), int(d), hour, minute, second, tzinfo=timezone.utc)


def _next_sign_change(jd: float) -> dict | None:
    """Find the next planet that crosses a sign boundary, scanning ~30 days."""
    candidates = []
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for name, pid in PLANET_IDS.items():
        long_now, _ = _planet_long(jd, pid)
        sign_now = int(long_now // 30) % 12
        cursor = jd
        # Scan in 1-day steps for fast-moving, longer for slow.
        max_days = {"Sun": 35, "Moon": 35, "Mars": 60, "Mercury": 35, "Venus": 35,
                    "Jupiter": 400, "Saturn": 900, "Rahu": 540}[name]
        for _ in range(int(max_days)):
            cursor += 1.0
            long_, _ = _planet_long(cursor, pid)
            sign_new = int(long_ // 30) % 12
            if sign_new != sign_now:
                candidates.append({
                    "planet": name,
                    "from": SIGNS[sign_now],
                    "to": SIGNS[sign_new],
                    "at": _jd_to_datetime(cursor).isoformat(),
                    "_jd": cursor,
                })
                break
    if not candidates:
        return None
    candidates.sort(key=lambda c: c["_jd"])
    nxt = candidates[0]
    nxt.pop("_jd", None)
    return nxt


def get_current_sky(
    as_of: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    """Return a generic sky snapshot for `as_of` (defaults to now UTC)."""
    if as_of is not None:
        as_of_dt = _parse_as_of(as_of)
    else:
        as_of_dt = _parse_as_of(None)
    jd = _to_jd(as_of_dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    planets = []
    retrogrades: list[str] = []
    for name, pid in PLANET_IDS.items():
        long_, retro = _planet_long(jd, pid)
        sign_idx = int(long_ // 30) % 12
        planets.append({
            "name": name,
            "sign": SIGNS[sign_idx],
            "degree": round(long_ % 30, 4),
            "retrograde": retro,
            "nakshatra": _nakshatra_for(long_),
        })
        if retro:
            retrogrades.append(name)

    # Ketu is Rahu + 180°
    rahu_entry = next(p for p in planets if p["name"] == "Rahu")
    rahu_long = SIGNS.index(rahu_entry["sign"]) * 30 + rahu_entry["degree"]
    ketu_long = (rahu_long + 180.0) % 360.0
    ketu_sign = SIGNS[int(ketu_long // 30) % 12]
    planets.append({
        "name": "Ketu",
        "sign": ketu_sign,
        "degree": round(ketu_long % 30, 4),
        "retrograde": True,
        "nakshatra": _nakshatra_for(ketu_long),
    })
    retrogrades.append("Ketu")

    illum = _illumination(jd)
    illum_next = _illumination(jd + 0.5)
    waxing = illum_next > illum
    moon_phase = {
        "name": _moon_phase_name(illum, waxing),
        "illumination": round(min(max(illum, 0.0), 1.0), 4),
        "next_full_moon": _next_extreme_moon(jd, "full").isoformat(),
        "next_new_moon": _next_extreme_moon(jd, "new").isoformat(),
    }

    nxt = _next_sign_change(jd)

    return {
        "as_of": as_of_dt.isoformat(),
        "planets": planets,
        "moon_phase": moon_phase,
        "retrogrades": retrogrades,
        "next_sign_change": nxt,
        "next_event": nxt,  # eclipse detection deferred — surface sign change as next event
    }


__all__ = ["get_current_sky"]
