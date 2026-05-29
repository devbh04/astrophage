"""
Panchang tool — five limbs of Panchang plus inauspicious windows.

Returns Tithi, Vara, Nakshatra, Yoga, Karana, Sunrise, Sunset, Rahu Kaal,
Yamaganda, Gulika, and Abhijit Muhurta for a given date and location.
All time values are ISO 8601 strings with timezone offsets.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone as _tz
from zoneinfo import ZoneInfo
import zoneinfo

import swisseph as swe

# ── Static tables ───────────────────────────────────────────────

TITHI_NAMES = [
    "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya", "Shukla Chaturthi",
    "Shukla Panchami", "Shukla Shashti", "Shukla Saptami", "Shukla Ashtami",
    "Shukla Navami", "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
    "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashti", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
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

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Aindra", "Vaidhriti",
]

KARANA_NAMES_FIXED = ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]
KARANA_NAMES_MOVABLE = [
    "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti",
]

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
VARA_VEDIC = ["Bhanuvara", "Somavara", "Mangalavara", "Budhavara", "Guruvara", "Shukravara", "Shanivara"]

# Rahu Kaal table — index by weekday (0=Sunday) → (start_eighth, end_eighth)
# Day is divided into 8 equal parts from sunrise to sunset.
RAHU_KAAL_PERIOD = {
    0: 8,  # Sunday: 8th period (last)
    1: 2,  # Monday: 2nd
    2: 7,  # Tuesday: 7th
    3: 5,  # Wednesday: 5th
    4: 6,  # Thursday: 6th
    5: 4,  # Friday: 4th
    6: 3,  # Saturday: 3rd
}

# Yamaganda Kaal periods (1-indexed eighths of day)
YAMAGANDA_PERIOD = {
    0: 5,  # Sunday
    1: 4,  # Monday
    2: 3,  # Tuesday
    3: 2,  # Wednesday
    4: 1,  # Thursday
    5: 7,  # Friday
    6: 6,  # Saturday
}

# Gulika Kaal periods
GULIKA_PERIOD = {
    0: 7,  # Sunday
    1: 6,  # Monday
    2: 5,  # Tuesday
    3: 4,  # Wednesday
    4: 3,  # Thursday
    5: 2,  # Friday
    6: 1,  # Saturday
}


# ── Helpers ─────────────────────────────────────────────────────


def _validate_inputs(date: str, lat: float, lng: float, timezone: str) -> ZoneInfo:
    if not isinstance(date, str) or len(date) < 10:
        raise ValueError(f"Malformed field 'date' (expected YYYY-MM-DD): {date!r}")
    try:
        datetime.strptime(date[:10], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Malformed field 'date': {date!r}") from exc
    if not (-90.0 <= lat <= 90.0):
        raise ValueError(f"Field 'lat' out of range [-90, 90]: {lat!r}")
    if not (-180.0 <= lng <= 180.0):
        raise ValueError(f"Field 'lng' out of range [-180, 180]: {lng!r}")
    try:
        return ZoneInfo(timezone)
    except (zoneinfo.ZoneInfoNotFoundError, Exception) as exc:
        raise ValueError(f"Field 'timezone' not an IANA zone: {timezone!r}") from exc


def _to_utc_jd(dt: datetime) -> float:
    dt_utc = dt.astimezone(_tz.utc)
    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _jd_to_local(jd: float, tz: ZoneInfo) -> datetime:
    """Convert a Julian Day (UTC) to a tz-aware local datetime."""
    y, m, d, frac = swe.revjul(jd)
    seconds_total = int(round(frac * 3600.0))
    hour, rem = divmod(seconds_total, 3600)
    minute, second = divmod(rem, 60)
    if hour == 24:
        # Roll over the day
        hour = 0
        dt_utc = datetime(int(y), int(m), int(d), 0, minute, second, tzinfo=_tz.utc) + timedelta(days=1)
    else:
        dt_utc = datetime(int(y), int(m), int(d), hour, minute, second, tzinfo=_tz.utc)
    return dt_utc.astimezone(tz)


def _sunrise_sunset(date: str, lat: float, lng: float, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Compute sunrise and sunset in local time using Swiss Ephemeris."""
    swe.set_topo(lng, lat, 0.0)
    # Anchor at local 00:00 → convert to UTC JD
    local_midnight = datetime.fromisoformat(f"{date}T00:00:00").replace(tzinfo=tz)
    jd_start = _to_utc_jd(local_midnight)
    geopos = (lng, lat, 0.0)

    def _rise_or_trans(flag: int) -> float:
        result = swe.rise_trans(jd_start, swe.SUN, flag, geopos)
        # Some swisseph versions return (retval, [tret]) and others return ([tret], retval).
        if isinstance(result, tuple):
            for item in result:
                if isinstance(item, (list, tuple)) and item and isinstance(item[0], float):
                    return float(item[0])
                if isinstance(item, float) and item > 1000:
                    return item
        return 0.0

    jd_rise = _rise_or_trans(swe.CALC_RISE)
    jd_set = _rise_or_trans(swe.CALC_SET)
    if jd_set <= jd_rise:
        # Search next day for sunset
        jd_set_next = swe.rise_trans(jd_rise + 0.01, swe.SUN, swe.CALC_SET, geopos)
        if isinstance(jd_set_next, tuple):
            for item in jd_set_next:
                if isinstance(item, (list, tuple)) and item:
                    jd_set = float(item[0]); break
                if isinstance(item, float) and item > 1000:
                    jd_set = item; break
    sunrise = _jd_to_local(jd_rise, tz)
    sunset = _jd_to_local(jd_set, tz)
    return sunrise, sunset


def _sun_moon_long_at(jd: float) -> tuple[float, float]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    sun_pos, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
    return sun_pos[0] % 360.0, moon_pos[0] % 360.0


def _tithi_index(sun_long: float, moon_long: float) -> tuple[int, float]:
    """Return (tithi_index 0..29, fraction-into-tithi)."""
    diff = (moon_long - sun_long) % 360.0
    span = 12.0
    idx = int(diff // span)
    frac = (diff - idx * span) / span
    return idx, frac


def _interval_end(
    base: datetime,
    progress_frac: float,
    span_seconds: float,
) -> datetime:
    """Estimate when an interval that has progressed `progress_frac` (0..1) will end."""
    remaining = max(0.0, (1.0 - progress_frac) * span_seconds)
    return base + timedelta(seconds=remaining)


# Approximate average durations
TITHI_AVG_SECONDS = 23.62 * 3600
NAK_AVG_SECONDS = 23.5 * 3600
YOGA_AVG_SECONDS = 22.0 * 3600
KARANA_AVG_SECONDS = TITHI_AVG_SECONDS / 2.0


def _karana_name(tithi_idx: int, half: int) -> str:
    """
    Karana index counted from Shukla Pratipada first half.
    There are 60 karanas in a synodic month; first half of Shukla Pratipada
    is fixed Kimstughna, last half of Krishna Chaturdashi is Shakuni, etc.
    """
    abs_index = tithi_idx * 2 + half  # 0..59
    # Fixed karanas:
    # 0 -> Kimstughna (first half of Shukla Pratipada)
    # 57 -> Shakuni (last half of Krishna Chaturdashi)
    # 58 -> Chatushpada (first half of Amavasya)
    # 59 -> Naga (last half of Amavasya)
    if abs_index == 0:
        return KARANA_NAMES_FIXED[3]  # Kimstughna
    if abs_index == 57:
        return KARANA_NAMES_FIXED[0]
    if abs_index == 58:
        return KARANA_NAMES_FIXED[1]
    if abs_index == 59:
        return KARANA_NAMES_FIXED[2]
    movable_idx = (abs_index - 1) % 7
    return KARANA_NAMES_MOVABLE[movable_idx]


def _split_day_eighths(sunrise: datetime, sunset: datetime, eighth_index_1based: int) -> tuple[datetime, datetime]:
    span = (sunset - sunrise) / 8
    start = sunrise + span * (eighth_index_1based - 1)
    return start, start + span


def get_panchang(
    date: str,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """Five limbs of Panchang plus inauspicious windows for a given date+place."""
    tz = _validate_inputs(date, lat, lng, timezone)

    sunrise, sunset = _sunrise_sunset(date, lat, lng, tz)
    jd_sunrise = _to_utc_jd(sunrise)
    sun_long, moon_long = _sun_moon_long_at(jd_sunrise)

    # Tithi
    tithi_idx, tithi_frac = _tithi_index(sun_long, moon_long)
    tithi_idx = tithi_idx % 30
    tithi_end = _interval_end(sunrise, tithi_frac, TITHI_AVG_SECONDS)
    tithi = {
        "name": TITHI_NAMES[tithi_idx],
        "number": tithi_idx + 1,
        "ends_at": tithi_end.isoformat(),
        "start": sunrise.isoformat(),
    }

    # Nakshatra
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_long // nak_span) % 27
    nak_pos = moon_long - nak_idx * nak_span
    nak_frac = nak_pos / nak_span
    nak_end = _interval_end(sunrise, nak_frac, NAK_AVG_SECONDS)
    nakshatra = {
        "name": NAKSHATRAS[nak_idx],
        "lord": NAKSHATRA_LORDS[nak_idx],
        "ends_at": nak_end.isoformat(),
        "start": sunrise.isoformat(),
    }

    # Yoga: (sun_long + moon_long) / yoga_span
    yoga_span = 360.0 / 27.0
    yoga_pos = (sun_long + moon_long) % 360.0
    yoga_idx = int(yoga_pos // yoga_span) % 27
    yoga_frac = (yoga_pos - yoga_idx * yoga_span) / yoga_span
    yoga_end = _interval_end(sunrise, yoga_frac, YOGA_AVG_SECONDS)
    yoga = {
        "name": YOGA_NAMES[yoga_idx],
        "number": yoga_idx + 1,
        "ends_at": yoga_end.isoformat(),
        "start": sunrise.isoformat(),
    }

    # Karana: each tithi has two halves
    karana_half = 0 if tithi_frac < 0.5 else 1
    karana_within_frac = (tithi_frac * 2.0) - karana_half
    karana_end = _interval_end(sunrise, karana_within_frac, KARANA_AVG_SECONDS)
    karana_name = _karana_name(tithi_idx, karana_half)
    karana = {
        "name": karana_name,
        "ends_at": karana_end.isoformat(),
        "start": sunrise.isoformat(),
    }

    # Vara
    weekday = sunrise.weekday()  # Monday=0..Sunday=6
    # Map Python's Monday=0 → Sunday=0 used for Rahu Kaal table
    sunday_based = (weekday + 1) % 7
    vara = {
        "name": VARA_VEDIC[sunday_based],
        "weekday": VARA_NAMES[sunday_based],
    }

    # Rahu Kaal / Yamaganda / Gulika
    rk_start, rk_end = _split_day_eighths(sunrise, sunset, RAHU_KAAL_PERIOD[sunday_based])
    yk_start, yk_end = _split_day_eighths(sunrise, sunset, YAMAGANDA_PERIOD[sunday_based])
    gk_start, gk_end = _split_day_eighths(sunrise, sunset, GULIKA_PERIOD[sunday_based])

    rahu_kaal = {"start": rk_start.isoformat(), "end": rk_end.isoformat(), "ends_at": rk_end.isoformat()}
    yamaganda = {"start": yk_start.isoformat(), "end": yk_end.isoformat(), "ends_at": yk_end.isoformat()}
    gulika = {"start": gk_start.isoformat(), "end": gk_end.isoformat(), "ends_at": gk_end.isoformat()}

    # Abhijit Muhurta — middle 48 minutes of the day
    midday = sunrise + (sunset - sunrise) / 2
    abhijit_start = midday - timedelta(minutes=24)
    abhijit_end = midday + timedelta(minutes=24)
    abhijit = {
        "start": abhijit_start.isoformat(),
        "end": abhijit_end.isoformat(),
        "ends_at": abhijit_end.isoformat(),
    }

    return {
        "tithi": tithi,
        "vara": vara,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karana": karana,
        "sunrise": sunrise.isoformat(),
        "sunset": sunset.isoformat(),
        "rahu_kaal": rahu_kaal,
        "yamaganda": yamaganda,
        "gulika": gulika,
        "abhijit_muhurta": abhijit,
    }


__all__ = ["get_panchang"]
