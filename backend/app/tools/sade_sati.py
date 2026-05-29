"""
Sade Sati and Ashtama Shani analysis tool.

Sade Sati is the ~7.5-year transit when Saturn occupies the natal Moon's sign
or its immediate neighbours (12th and 2nd from the Moon). Ashtama Shani is
Saturn in the 8th from the natal Moon.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import swisseph as swe

from app.tools.dasha import _parse_as_of  # type: ignore

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_index(sign: str) -> int:
    try:
        return SIGNS.index(sign)
    except ValueError as exc:
        raise ValueError(f"Unknown sign: {sign!r}") from exc


def _natal_moon_sign_index(natal_chart: dict) -> int:
    moon_sign = natal_chart.get("moon_sign")
    if moon_sign:
        return _sign_index(moon_sign)
    for planet in natal_chart.get("planets", []) or []:
        if planet.get("name") == "Moon":
            return _sign_index(planet["sign"])
    raise ValueError("natal_chart is missing the Moon's sign")


def _saturn_sign_index_at(as_of_dt: datetime) -> int:
    """Compute Saturn's sidereal sign index at `as_of_dt` via Swiss Ephemeris."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(
        as_of_dt.year,
        as_of_dt.month,
        as_of_dt.day,
        as_of_dt.hour + as_of_dt.minute / 60.0 + as_of_dt.second / 3600.0,
    )
    pos, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
    return int(pos[0] // 30) % 12


def sade_sati_phase(natal_moon_sign_idx: int, saturn_sign_idx: int) -> str:
    """Return the Sade Sati phase string given two sign indices in [0, 12)."""
    diff = (saturn_sign_idx - natal_moon_sign_idx) % 12
    if diff == 11:
        return "rising"
    if diff == 0:
        return "peak"
    if diff == 1:
        return "setting"
    return "none"


def _is_ashtama_shani(natal_moon_sign_idx: int, saturn_sign_idx: int) -> bool:
    return (saturn_sign_idx - natal_moon_sign_idx) % 12 == 7


# Saturn moves through 12 signs in ~29.5 years → ~2.46 years per sign.
SATURN_YEARS_PER_SIGN = 29.5 / 12.0


def _phase_window(natal_moon_sign_idx: int, as_of: datetime) -> dict:
    """
    Estimate (start, peak_start, end) for the *current* Sade Sati occurrence.

    We do this by stepping Saturn backwards/forwards from `as_of` in 30-day
    increments and detecting the sign-boundary crossings. This is a coarse
    estimate (sign boundaries dominate Saturn's slow motion); refining with
    retrograde wobble is left to a future task.
    """
    saturn_now = _saturn_sign_index_at(as_of)
    phase = sade_sati_phase(natal_moon_sign_idx, saturn_now)
    if phase == "none":
        return {"start": None, "peak_start": None, "end": None, "phase": "none"}

    # Walk backward to find when Saturn entered the rising sign.
    rising_sign = (natal_moon_sign_idx + 11) % 12
    peak_sign = natal_moon_sign_idx
    setting_sign = (natal_moon_sign_idx + 1) % 12

    def step(direction: int, target_sign: int, anchor: datetime) -> datetime:
        cursor = anchor
        last_idx = _saturn_sign_index_at(cursor)
        for _ in range(0, 60):  # cap at ~5 years of 30-day steps each side
            cursor = cursor + timedelta(days=30 * direction)
            idx = _saturn_sign_index_at(cursor)
            if idx != last_idx:
                if idx == target_sign:
                    return cursor
                last_idx = idx
        return cursor

    # Backward to start of rising
    backward_anchor = as_of
    while _saturn_sign_index_at(backward_anchor) != rising_sign:
        backward_anchor = backward_anchor - timedelta(days=30)
        # Safety break
        if (as_of - backward_anchor).days > 365 * 4:
            break
    start = backward_anchor
    while _saturn_sign_index_at(start - timedelta(days=30)) == rising_sign:
        start = start - timedelta(days=30)
        if (as_of - start).days > 365 * 4:
            break

    # Find peak start (Saturn enters Moon's sign).
    peak_anchor = as_of
    if _saturn_sign_index_at(peak_anchor) == peak_sign:
        # walk back to the boundary
        while _saturn_sign_index_at(peak_anchor - timedelta(days=30)) == peak_sign:
            peak_anchor = peak_anchor - timedelta(days=30)
            if (as_of - peak_anchor).days > 365 * 4:
                break
    else:
        # Walk forward to find boundary
        peak_anchor = step(1, peak_sign, as_of)

    # Find end (Saturn leaves setting sign).
    end_anchor = as_of
    while _saturn_sign_index_at(end_anchor) in (rising_sign, peak_sign, setting_sign):
        end_anchor = end_anchor + timedelta(days=30)
        if (end_anchor - as_of).days > 365 * 8:
            break

    return {
        "start": start.isoformat(),
        "peak_start": peak_anchor.isoformat(),
        "end": end_anchor.isoformat(),
        "phase": phase,
    }


def _historical_occurrences(
    natal_moon_sign_idx: int,
    as_of: datetime,
    look_back_years: int = 60,
) -> list[dict]:
    """Walk backward 60 years and detect prior Sade Sati spans."""
    history: list[dict] = []
    cursor = as_of - timedelta(days=int(look_back_years * 365.25))
    in_phase = False
    span_start: datetime | None = None
    span_phase = "none"
    while cursor < as_of:
        sat = _saturn_sign_index_at(cursor)
        ph = sade_sati_phase(natal_moon_sign_idx, sat)
        if ph != "none":
            if not in_phase:
                in_phase = True
                span_start = cursor
                span_phase = ph
        else:
            if in_phase and span_start is not None:
                history.append({
                    "start": span_start.isoformat(),
                    "end": cursor.isoformat(),
                    "phase": span_phase,
                    "intensity": _intensity(span_phase),
                })
                in_phase = False
                span_start = None
        cursor = cursor + timedelta(days=180)
    return history


def _intensity(phase: str) -> str:
    return {"rising": "moderate", "peak": "high", "setting": "moderate"}.get(phase, "low")


def check_sade_sati(natal_chart: dict, as_of: str | None = None) -> dict:
    """Return a Sade Sati / Ashtama Shani analysis for a natal chart at `as_of`."""
    natal_idx = _natal_moon_sign_index(natal_chart)
    as_of_dt = _parse_as_of(as_of)

    # Allow injection of a precomputed Saturn sign for testing or for charts
    # that already carry a transit snapshot.
    if "saturn_sign" in natal_chart and as_of is None:
        saturn_idx = _sign_index(natal_chart["saturn_sign"])
    else:
        try:
            saturn_idx = _saturn_sign_index_at(as_of_dt)
        except Exception:
            saturn_idx = _sign_index(natal_chart.get("saturn_sign", "Aries"))

    phase = sade_sati_phase(natal_idx, saturn_idx)
    in_sade_sati = phase != "none"
    ashtama = _is_ashtama_shani(natal_idx, saturn_idx)

    if in_sade_sati:
        try:
            window = _phase_window(natal_idx, as_of_dt)
        except Exception:
            window = {"start": None, "peak_start": None, "end": None, "phase": phase}
    else:
        window = {"start": None, "peak_start": None, "end": None, "phase": "none"}

    if in_sade_sati:
        current_status = (
            f"Saturn in sign offset {(saturn_idx - natal_idx) % 12} from your natal Moon "
            f"({phase} phase)"
        )
    else:
        current_status = "Not currently in Sade Sati"

    history: list[dict[str, Any]] = []
    if as_of is None:
        try:
            history = _historical_occurrences(natal_idx, as_of_dt, look_back_years=60)
        except Exception:
            history = []

    return {
        "in_sade_sati": in_sade_sati,
        "phase": phase,
        "current_status": current_status,
        "ashtama_shani": ashtama,
        "start": window.get("start"),
        "peak_start": window.get("peak_start"),
        "end": window.get("end"),
        "history": history,
    }


__all__ = ["check_sade_sati", "sade_sati_phase"]
