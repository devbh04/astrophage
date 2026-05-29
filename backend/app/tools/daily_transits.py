"""
Daily Transits tool — current planetary positions vs. natal chart.

For each of the nine grahas: returns its current sidereal sign + house from
lagna, the natal sign + house, an aspect-to-natal block, an intensity tag,
and a textual interpretation. Also returns `activated_houses` and a
headline.
"""

from __future__ import annotations

from datetime import datetime, timezone

import swisseph as swe

from app.tools.dasha import _parse_as_of, NAK_SPAN
from app.tools.current_sky import (
    PLANET_IDS,
    SIGNS,
    _to_jd,
    _planet_long,
    _nakshatra_for,
)


def _natal_planet_lookup(natal_chart: dict) -> dict[str, dict]:
    return {p["name"]: p for p in natal_chart.get("planets", []) or []}


def _ascendant_sign_index(natal_chart: dict) -> int:
    asc = natal_chart.get("ascendant", {})
    sign = asc.get("sign") if isinstance(asc, dict) else None
    if sign and sign in SIGNS:
        return SIGNS.index(sign)
    return 0


def _house_from(asc_idx: int, sign_idx: int) -> int:
    return ((sign_idx - asc_idx) % 12) + 1


def _aspects(planet: str, current_sign_idx: int, natal: dict[str, dict]) -> list[dict]:
    """Crude aspect detection — same sign / 7th / 5th / 9th from natal positions."""
    aspect_offsets = {
        "conjunction": 0, "7th": 6, "5th": 4, "9th": 8, "3rd": 2,
    }
    out: list[dict] = []
    for target_name, target in natal.items():
        if target_name == planet:
            continue
        try:
            target_sign_idx = SIGNS.index(target["sign"])
        except (ValueError, KeyError):
            continue
        for label, off in aspect_offsets.items():
            if (current_sign_idx - target_sign_idx) % 12 == off:
                out.append({
                    "target": target_name,
                    "type": label,
                    "strength": 0.8 if label in ("conjunction", "7th") else 0.5,
                })
                break
    return out


def _intensity(aspects: list[dict]) -> str:
    if not aspects:
        return "low"
    max_strength = max(a["strength"] for a in aspects)
    if max_strength >= 0.8:
        return "high"
    if max_strength >= 0.5:
        return "medium"
    return "low"


def get_daily_transits(
    natal_chart: dict,
    as_of: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    """Return current planetary transits relative to a natal chart."""
    as_of_dt = _parse_as_of(as_of) if as_of is not None else _parse_as_of(None)
    jd = _to_jd(as_of_dt)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    asc_idx = _ascendant_sign_index(natal_chart)
    natal_lookup = _natal_planet_lookup(natal_chart)

    transits: list[dict] = []
    activated: set[int] = set()

    for name, pid in PLANET_IDS.items():
        long_, retro = _planet_long(jd, pid)
        sign_idx = int(long_ // 30) % 12
        house = _house_from(asc_idx, sign_idx)
        natal = natal_lookup.get(name, {})
        natal_sign = natal.get("sign", "Unknown")
        natal_house = natal.get("house", 0)
        aspects = _aspects(name, sign_idx, natal_lookup)
        intensity = _intensity(aspects)
        activated.add(house)
        for asp in aspects:
            try:
                target_sign_idx = SIGNS.index(natal_lookup[asp["target"]]["sign"])
                activated.add(_house_from(asc_idx, target_sign_idx))
            except (KeyError, ValueError):
                continue
        interpretation = (
            f"{name} is transiting {SIGNS[sign_idx]} (house {house} from your Lagna), "
            f"natally placed in {natal_sign} (house {natal_house}). "
            f"{'Retrograde — ' if retro else ''}intensity: {intensity}."
        )
        transits.append({
            "planet": name,
            "current_sign": SIGNS[sign_idx],
            "current_house_from_lagna": house,
            "natal_sign": natal_sign,
            "natal_house": natal_house,
            "aspects_natal": aspects,
            "intensity": intensity,
            "interpretation": interpretation,
            "retrograde": retro,
            "current_nakshatra": _nakshatra_for(long_),
        })

    # Add Ketu (180° from Rahu in transits)
    rahu_entry = next((t for t in transits if t["planet"] == "Rahu"), None)
    if rahu_entry:
        rahu_sign_idx = SIGNS.index(rahu_entry["current_sign"])
        ketu_sign_idx = (rahu_sign_idx + 6) % 12
        ketu_house = _house_from(asc_idx, ketu_sign_idx)
        natal = natal_lookup.get("Ketu", {})
        transits.append({
            "planet": "Ketu",
            "current_sign": SIGNS[ketu_sign_idx],
            "current_house_from_lagna": ketu_house,
            "natal_sign": natal.get("sign", "Unknown"),
            "natal_house": natal.get("house", 0),
            "aspects_natal": _aspects("Ketu", ketu_sign_idx, natal_lookup),
            "intensity": "medium",
            "interpretation": (
                f"Ketu is transiting {SIGNS[ketu_sign_idx]} (house {ketu_house} from your Lagna)."
            ),
            "retrograde": True,
            "current_nakshatra": _nakshatra_for(ketu_sign_idx * 30),
        })
        activated.add(ketu_house)

    activated_houses = sorted(h for h in activated if 1 <= h <= 12)

    # Headline: pick the strongest planet's interpretation
    strongest = max(
        transits, key=lambda t: 1 if t["intensity"] == "high" else 0,
        default=transits[0] if transits else None,
    )
    headline = (
        f"{strongest['planet']} activates your {strongest['current_sign']} "
        f"({strongest['intensity']} intensity)" if strongest else ""
    )

    return {
        "as_of": as_of_dt.isoformat(),
        "transits": transits,
        "activated_houses": activated_houses,
        "headline": headline,
    }


__all__ = ["get_daily_transits"]
