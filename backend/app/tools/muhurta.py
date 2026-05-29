"""
Muhurta finder — score 30-minute candidate windows across a date range
against a per-purpose Panchang rubric, and return the top 3.

Excludes any window overlapping the same day's Rahu Kaal or Yamaganda.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Iterable

from app.tools.panchang import get_panchang


VALID_PURPOSES = {"wedding", "travel", "business_start", "griha_pravesh", "general"}


# Per-purpose nakshatra preferences. Higher weight → more auspicious.
NAKSHATRA_RUBRIC: dict[str, dict[str, float]] = {
    "wedding": {
        "Rohini": 1.0, "Mrigashira": 0.9, "Magha": 0.8, "Hasta": 1.0,
        "Swati": 0.9, "Anuradha": 1.0, "Mula": 0.7, "Uttara Phalguni": 0.95,
        "Uttara Ashadha": 0.95, "Uttara Bhadrapada": 0.9, "Revati": 0.85,
    },
    "travel": {
        "Ashwini": 1.0, "Pushya": 1.0, "Punarvasu": 0.95, "Hasta": 0.9,
        "Anuradha": 0.85, "Shravana": 1.0, "Dhanishta": 0.9, "Revati": 0.95,
    },
    "business_start": {
        "Pushya": 1.0, "Hasta": 0.95, "Chitra": 0.9, "Anuradha": 0.85,
        "Uttara Phalguni": 0.9, "Uttara Ashadha": 0.95, "Uttara Bhadrapada": 0.9,
        "Shravana": 0.95, "Dhanishta": 0.9,
    },
    "griha_pravesh": {
        "Rohini": 1.0, "Mrigashira": 0.9, "Hasta": 0.95, "Anuradha": 0.95,
        "Uttara Phalguni": 0.9, "Uttara Ashadha": 0.95, "Uttara Bhadrapada": 0.9,
        "Revati": 0.85, "Pushya": 1.0,
    },
    "general": {
        "Pushya": 0.9, "Hasta": 0.85, "Anuradha": 0.85, "Rohini": 0.85,
        "Shravana": 0.85, "Revati": 0.8,
    },
}

INAUSPICIOUS_NAKSHATRAS = {"Bharani", "Ashlesha", "Magha", "Jyeshtha", "Mula"}

# Tithi preferences: numbers 1..30 (1 = Shukla Pratipada, 15 = Purnima, 30 = Amavasya)
TITHI_AUSPICIOUS = {2, 3, 5, 7, 10, 11, 13}  # Nanda, Bhadra, Jaya, Rikta excluded
TITHI_INAUSPICIOUS = {4, 9, 14, 30, 8, 15}  # Rikta + Amavasya + Purnima depending on use


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _interval_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _score_window(
    start: datetime,
    end: datetime,
    panchang_today: dict,
    purpose: str,
) -> tuple[float, dict]:
    nakshatra_name = panchang_today["nakshatra"]["name"]
    tithi_no = panchang_today["tithi"]["number"]
    yoga_name = panchang_today["yoga"]["name"]
    weekday = panchang_today["vara"]["weekday"]

    rubric = NAKSHATRA_RUBRIC.get(purpose, NAKSHATRA_RUBRIC["general"])
    nak_w = rubric.get(nakshatra_name, 0.4)
    if nakshatra_name in INAUSPICIOUS_NAKSHATRAS:
        nak_w = min(nak_w, 0.2)

    tithi_w = 1.0 if tithi_no in TITHI_AUSPICIOUS else (0.2 if tithi_no in TITHI_INAUSPICIOUS else 0.6)

    yoga_w = 0.9 if yoga_name in {"Siddha", "Shubha", "Vriddhi", "Dhruva", "Saubhagya"} else 0.6
    if yoga_name in {"Vyatipata", "Vaidhriti", "Atiganda"}:
        yoga_w = 0.2

    weekday_w = {
        "wedding": {"Monday": 0.9, "Wednesday": 0.85, "Thursday": 1.0, "Friday": 1.0,
                     "Sunday": 0.6, "Tuesday": 0.4, "Saturday": 0.4},
        "travel": {"Monday": 0.9, "Wednesday": 1.0, "Thursday": 0.9,
                    "Friday": 0.8, "Sunday": 0.6, "Tuesday": 0.5, "Saturday": 0.4},
        "business_start": {"Wednesday": 1.0, "Thursday": 1.0, "Friday": 0.9,
                            "Monday": 0.7, "Sunday": 0.6, "Tuesday": 0.5, "Saturday": 0.4},
        "griha_pravesh": {"Monday": 0.9, "Wednesday": 0.9, "Thursday": 1.0,
                           "Friday": 1.0, "Sunday": 0.6, "Tuesday": 0.4, "Saturday": 0.5},
        "general": {d: 0.7 for d in
                     ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
    }
    wd_w = weekday_w.get(purpose, weekday_w["general"]).get(weekday, 0.5)

    # Abhijit overlap bonus
    abhijit = panchang_today.get("abhijit_muhurta") or {}
    abhijit_bonus = 0.0
    try:
        ab_start = datetime.fromisoformat(abhijit["start"])
        ab_end = datetime.fromisoformat(abhijit["end"])
        if _interval_overlap(start, end, ab_start, ab_end):
            abhijit_bonus = 0.1
    except Exception:
        pass

    score = (
        0.30 * nak_w + 0.25 * tithi_w + 0.20 * yoga_w + 0.15 * wd_w + 0.10 + abhijit_bonus
    )
    score = max(0.0, min(1.0, score))

    factors = {
        "tithi": f"{panchang_today['tithi']['name']} ({'favorable' if tithi_w > 0.5 else 'mixed'})",
        "nakshatra": f"{nakshatra_name} ({'auspicious' if nak_w > 0.6 else 'mixed'})",
        "yoga": f"{yoga_name} ({'excellent' if yoga_w > 0.8 else 'okay'})",
        "weekday": weekday,
        "rahu_kaal_clash": False,
        "abhijit_overlap": abhijit_bonus > 0,
    }
    return score, factors


def compute_muhurta(
    purpose: str,
    start_date: str,
    end_date: str,
    lat: float,
    lng: float,
    timezone: str,
) -> dict:
    """Find top auspicious 30-minute windows for a purpose in [start_date, end_date]."""
    if purpose not in VALID_PURPOSES:
        # Treat unknown purpose as 'general'
        purpose = "general"

    sd = _parse_date(start_date)
    ed = _parse_date(end_date)
    if ed < sd:
        raise ValueError(f"end_date {end_date!r} is before start_date {start_date!r}")
    if (ed - sd).days > 365:
        raise ValueError("Muhurta date range cannot exceed 365 days")

    tz = ZoneInfo(timezone)
    sd_local = datetime.fromisoformat(start_date).replace(tzinfo=tz)
    ed_local = datetime.fromisoformat(end_date).replace(tzinfo=tz) + timedelta(days=1)

    candidates: list[dict] = []
    cursor_day = sd_local
    while cursor_day < ed_local:
        date_str = cursor_day.strftime("%Y-%m-%d")
        try:
            panchang_today = get_panchang(date_str, lat, lng, timezone)
        except Exception:
            cursor_day = cursor_day + timedelta(days=1)
            continue

        sunrise = datetime.fromisoformat(panchang_today["sunrise"])
        sunset = datetime.fromisoformat(panchang_today["sunset"])
        rk_start = datetime.fromisoformat(panchang_today["rahu_kaal"]["start"])
        rk_end = datetime.fromisoformat(panchang_today["rahu_kaal"]["end"])
        yk_start = datetime.fromisoformat(panchang_today["yamaganda"]["start"])
        yk_end = datetime.fromisoformat(panchang_today["yamaganda"]["end"])

        # Walk 30-min windows from sunrise to sunset
        cursor = sunrise
        while cursor + timedelta(minutes=30) <= sunset:
            w_start = cursor
            w_end = cursor + timedelta(minutes=30)
            cursor = w_end
            if _interval_overlap(w_start, w_end, rk_start, rk_end):
                continue
            if _interval_overlap(w_start, w_end, yk_start, yk_end):
                continue
            score, factors = _score_window(w_start, w_end, panchang_today, purpose)
            candidates.append({
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "duration_minutes": 30,
                "score": round(score, 4),
                "factors": factors,
                "summary": (
                    f"{factors['nakshatra']}, {factors['tithi']}, {factors['yoga']}, "
                    f"{factors['weekday']}"
                ),
            })

        cursor_day = cursor_day + timedelta(days=1)

    # Top 3 by score
    candidates.sort(key=lambda w: w["score"], reverse=True)
    top = candidates[:3]

    return {
        "purpose": purpose,
        "windows": top,
    }


__all__ = ["compute_muhurta", "VALID_PURPOSES"]
