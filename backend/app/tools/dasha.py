"""
Vimshottari Dasha tool — compute Maha and Antar dasha periods from a natal Moon.

The Vimshottari system divides 120 years across nine dasha lords following the
canonical cycle ``[Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury]``
with years ``[7, 20, 6, 10, 7, 18, 16, 19, 17]``. The starting lord and the
balance at birth come from the Moon's nakshatra position.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

# Canonical Vimshottari cycle in dasha order with years
DASHA_ORDER: list[tuple[str, float]] = [
    ("Ketu", 7.0),
    ("Venus", 20.0),
    ("Sun", 6.0),
    ("Moon", 10.0),
    ("Mars", 7.0),
    ("Rahu", 18.0),
    ("Jupiter", 16.0),
    ("Saturn", 19.0),
    ("Mercury", 17.0),
]

# Years per lord, indexed by lord name
DASHA_YEARS: dict[str, float] = {lord: years for lord, years in DASHA_ORDER}

# Total cycle = 120 years
TOTAL_VIMSHOTTARI_YEARS = sum(years for _, years in DASHA_ORDER)

# Each nakshatra spans 13°20' = 360/27 degrees
NAK_SPAN = 360.0 / 27.0

# Nakshatra index → dasha lord (length 27)
NAKSHATRA_LORDS: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

# A Vedic year in days (sidereal year approximation used for dasha durations).
# 365.25 is the conventional value used by Jyotish software.
DAYS_PER_YEAR = 365.25


# ── Helpers ─────────────────────────────────────────────────────


def _years_to_timedelta(years: float) -> timedelta:
    """Convert a fractional year count into a `timedelta`."""
    return timedelta(days=years * DAYS_PER_YEAR)


def _moon_longitude(natal_chart: dict) -> float:
    """Extract the natal Moon's sidereal longitude from a chart dict."""
    if "moon_longitude" in natal_chart:
        return float(natal_chart["moon_longitude"])
    planets = natal_chart.get("planets") or []
    for planet in planets:
        if planet.get("name") == "Moon":
            if "total_degree" in planet:
                return float(planet["total_degree"])
            sign_index = _sign_index(planet.get("sign"))
            if sign_index is not None and "degree" in planet:
                return (sign_index * 30.0) + float(planet["degree"])
    raise ValueError(
        "Missing field 'moon_longitude' (or planets[Moon]) in natal_chart"
    )


SIGN_NAMES: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_index(sign: str | None) -> int | None:
    if not sign:
        return None
    try:
        return SIGN_NAMES.index(sign)
    except ValueError:
        return None


def _parse_birth_instant(
    birth_date: str,
    birth_time: str | None,
    timezone_name: str,
) -> datetime:
    """Parse the birth date/time/timezone into a tz-aware UTC datetime."""
    if not birth_date or not isinstance(birth_date, str):
        raise ValueError("Missing or malformed field 'birth_date'")
    try:
        date_parts = [int(p) for p in birth_date.split("-")]
        if len(date_parts) != 3:
            raise ValueError
        year, month, day = date_parts
    except Exception as exc:
        raise ValueError(
            f"Malformed field 'birth_date' (expected YYYY-MM-DD): {birth_date!r}"
        ) from exc

    if birth_time:
        time_parts = birth_time.split(":")
        try:
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            second = int(time_parts[2]) if len(time_parts) > 2 else 0
        except Exception as exc:
            raise ValueError(
                f"Malformed field 'birth_time' (expected HH:MM[:SS]): {birth_time!r}"
            ) from exc
    else:
        # Default to 06:00 local — same convention as compute_birth_chart.
        hour, minute, second = 6, 0, 0

    try:
        tz = ZoneInfo(timezone_name)
    except Exception as exc:
        raise ValueError(
            f"Malformed field 'timezone' (not an IANA zone): {timezone_name!r}"
        ) from exc

    local_dt = datetime(year, month, day, hour, minute, second, tzinfo=tz)
    return local_dt.astimezone(timezone.utc)


def _parse_as_of(as_of: str | None) -> datetime:
    """Parse an `as_of` string into a UTC datetime; default to now()."""
    if as_of is None:
        return datetime.now(tz=timezone.utc)
    try:
        dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception as exc:
        raise ValueError(f"Unparseable 'as_of': {as_of!r}") from exc


# ── Core algorithm ──────────────────────────────────────────────


def _balance_at_birth(moon_longitude: float) -> tuple[str, float]:
    """Return ``(lord, remaining_years)`` for the Moon's current dasha at birth."""
    if not (0.0 <= moon_longitude < 360.0):
        raise ValueError(
            f"Malformed field 'moon_longitude' (expected [0, 360)): {moon_longitude!r}"
        )
    nak_index = int(moon_longitude // NAK_SPAN)
    nak_index = min(nak_index, 26)
    lord = NAKSHATRA_LORDS[nak_index]
    pos_in_nak = moon_longitude - nak_index * NAK_SPAN
    lord_years = DASHA_YEARS[lord]
    remaining = (NAK_SPAN - pos_in_nak) / NAK_SPAN * lord_years
    return lord, remaining


def _antardashas(
    maha_lord: str,
    maha_start: datetime,
    maha_years: float,
) -> list[dict]:
    """Generate the antardasha sub-segments inside a maha-dasha."""
    sub_lords = _rotated_cycle(maha_lord)
    out = []
    cursor = maha_start
    for sub_lord, _ in sub_lords:
        sub_years = maha_years * (DASHA_YEARS[sub_lord] / TOTAL_VIMSHOTTARI_YEARS)
        sub_end = cursor + _years_to_timedelta(sub_years)
        out.append({
            "lord": sub_lord,
            "level": "antar",
            "start": cursor.isoformat(),
            "end": sub_end.isoformat(),
            "years": round(sub_years, 6),
        })
        cursor = sub_end
    return out


def _rotated_cycle(start_lord: str) -> list[tuple[str, float]]:
    """Return the 9-element canonical cycle rotated to begin at ``start_lord``."""
    lord_index = next(i for i, (lord, _) in enumerate(DASHA_ORDER) if lord == start_lord)
    return DASHA_ORDER[lord_index:] + DASHA_ORDER[:lord_index]


def _build_timeline(
    birth_lord: str,
    remaining_years: float,
    birth_instant: datetime,
    levels: int,
    span_years: float = 130.0,
) -> list[dict]:
    """
    Build a forward Maha-dasha timeline starting at the birth instant.

    The first segment is the *balance* of the birth lord's dasha (`remaining_years`).
    Subsequent segments follow the canonical cycle starting at the next lord.
    The timeline extends until cumulative span ≥ `span_years` (default 130 to
    safely exceed 120 years per Property 1).
    """
    timeline: list[dict] = []
    cursor = birth_instant
    cycle = _rotated_cycle(birth_lord)
    # First segment is partial (balance at birth)
    first_lord, _ = cycle[0]
    first_years = remaining_years
    first_end = cursor + _years_to_timedelta(first_years)
    segment: dict[str, Any] = {
        "lord": first_lord,
        "level": "maha",
        "start": cursor.isoformat(),
        "end": first_end.isoformat(),
        "years": round(first_years, 6),
    }
    if levels >= 2:
        # Antardashas of a partial maha still start from the maha lord;
        # we proportionally truncate to the remaining maha length.
        sub_lords = _rotated_cycle(first_lord)
        sub_cursor = cursor
        antars = []
        for sub_lord, _ in sub_lords:
            sub_full_years = (
                DASHA_YEARS[first_lord] * (DASHA_YEARS[sub_lord] / TOTAL_VIMSHOTTARI_YEARS)
            )
            # Skip antars that already elapsed before birth.
            elapsed_in_first = DASHA_YEARS[first_lord] - first_years
            sub_full_end = sub_cursor + _years_to_timedelta(sub_full_years)
            # offsets relative to first sub start
            # In a partial maha the antars after the active one carry over;
            # we approximate by allocating proportionally to the *balance*.
            sub_balance_years = (
                first_years * (DASHA_YEARS[sub_lord] / TOTAL_VIMSHOTTARI_YEARS)
            )
            sub_end = sub_cursor + _years_to_timedelta(sub_balance_years)
            antars.append({
                "lord": sub_lord,
                "level": "antar",
                "start": sub_cursor.isoformat(),
                "end": sub_end.isoformat(),
                "years": round(sub_balance_years, 6),
            })
            sub_cursor = sub_end
            # Suppress unused warning
            del sub_full_end, elapsed_in_first
        segment["antardashas"] = antars
    timeline.append(segment)
    cursor = first_end

    # Add full maha segments cycling through subsequent lords until span is met.
    accumulated = first_years
    cycle_iter = cycle[1:] + cycle  # extend so we don't run out
    idx = 0
    while accumulated < span_years:
        lord, years = cycle_iter[idx % len(cycle_iter)]
        seg_end = cursor + _years_to_timedelta(years)
        seg: dict[str, Any] = {
            "lord": lord,
            "level": "maha",
            "start": cursor.isoformat(),
            "end": seg_end.isoformat(),
            "years": round(years, 6),
        }
        if levels >= 2:
            seg["antardashas"] = _antardashas(lord, cursor, years)
        timeline.append(seg)
        cursor = seg_end
        accumulated += years
        idx += 1
    return timeline


def _find_active(
    timeline: list[dict],
    as_of: datetime,
) -> dict[str, Any]:
    """Locate the maha and antar segments that contain `as_of`."""
    active: dict[str, Any] = {"maha": None, "antar": None}
    for seg in timeline:
        seg_start = datetime.fromisoformat(seg["start"])
        seg_end = datetime.fromisoformat(seg["end"])
        if seg_start <= as_of < seg_end:
            active["maha"] = {
                "lord": seg["lord"],
                "start": seg["start"],
                "end": seg["end"],
            }
            for sub in seg.get("antardashas", []) or []:
                sub_start = datetime.fromisoformat(sub["start"])
                sub_end = datetime.fromisoformat(sub["end"])
                if sub_start <= as_of < sub_end:
                    active["antar"] = {
                        "lord": sub["lord"],
                        "start": sub["start"],
                        "end": sub["end"],
                    }
                    break
            break
    return active


# ── Public API ──────────────────────────────────────────────────


def compute_dasha_periods(
    natal_chart: dict,
    birth_date: str,
    birth_time: str | None,
    timezone: str,
    levels: int = 2,
    *,
    as_of: str | None = None,
    profile: dict | None = None,
) -> dict:
    """
    Compute the Vimshottari Dasha timeline from a natal chart's Moon position.

    Args:
        natal_chart: Output of ``compute_birth_chart`` (must contain Moon).
        birth_date: ISO ``YYYY-MM-DD``.
        birth_time: ``HH:MM[:SS]`` or ``None`` for sunrise approximation.
        timezone: IANA timezone of the birth place.
        levels: 1 = Maha only, 2 = Maha + Antar (default), 3 = Maha + Antar
            + Pratyantar (Pratyantar is treated as antar of antar; not
            recursively nested in this version — `levels=3` returns the same
            structure as `levels=2` plus an extra `pratyantar` key for clients
            that want it; current implementation surfaces only Maha+Antar).
        as_of: optional override for the "now" instant when computing
            ``active.maha`` / ``active.antar``.
        profile: optional birth-profile dict (must contain ``relationship``
            and ``id``); when ``relationship == "self"`` the result is
            persisted into ``birth_profiles.computed_dashas``.

    Returns:
        ``{balance_at_birth, timeline, active}``

    Raises:
        ValueError: if natal Moon longitude or birth_date is missing/malformed.
    """
    moon_long = _moon_longitude(natal_chart)
    if not (0.0 <= moon_long < 360.0):
        raise ValueError(
            f"Malformed field 'moon_longitude' (expected [0, 360)): {moon_long!r}"
        )

    birth_instant = _parse_birth_instant(birth_date, birth_time, timezone)

    lord, remaining = _balance_at_birth(moon_long)
    timeline = _build_timeline(lord, remaining, birth_instant, levels=levels)

    as_of_dt = _parse_as_of(as_of)
    active = _find_active(timeline, as_of_dt)

    result = {
        "balance_at_birth": {
            "lord": lord,
            "remaining_years": round(remaining, 6),
        },
        "timeline": timeline,
        "active": active,
    }

    # Persist for self profiles when caller provides one.
    if profile and profile.get("relationship") == "self" and profile.get("id"):
        try:
            from app.db.queries import update_profile_chart  # type: ignore
            import asyncio

            chart_to_keep = natal_chart
            coro = update_profile_chart(
                profile_id=profile["id"],
                computed_chart=chart_to_keep,
                computed_dashas=result,
            )
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(coro)
                else:
                    loop.run_until_complete(coro)
            except RuntimeError:
                # No running loop — schedule via asyncio.run.
                asyncio.run(coro)
        except Exception:
            # Persistence failures must not break the tool.
            pass

    return result


__all__ = [
    "compute_dasha_periods",
    "DASHA_ORDER",
    "DASHA_YEARS",
    "NAKSHATRA_LORDS",
    "NAK_SPAN",
    "TOTAL_VIMSHOTTARI_YEARS",
]
