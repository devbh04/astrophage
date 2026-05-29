"""
Kundali Milan tool — Ashtakoota 8-fold compatibility scoring + Mangal Dosha.

Returns sub-scores in their canonical ranges, a `total` in [0, 36],
a verdict, a Mangal Dosha block, warnings, and a textual summary.
"""

from __future__ import annotations

from app.tools.dasha import NAKSHATRA_LORDS, NAK_SPAN
from app.tools.nakshatra import NAKSHATRAS, NAKSHATRA_TABLE


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# ── Helpers ─────────────────────────────────────────────────────


def _moon_longitude(chart: dict) -> float:
    if "moon_longitude" in chart:
        return float(chart["moon_longitude"])
    for p in chart.get("planets", []) or []:
        if p.get("name") == "Moon":
            if "total_degree" in p:
                return float(p["total_degree"])
            sign_idx = SIGNS.index(p["sign"])
            return sign_idx * 30 + float(p.get("degree", 0))
    raise ValueError("chart is missing the Moon")


def _moon_sign_index(chart: dict) -> int:
    if "moon_sign" in chart:
        return SIGNS.index(chart["moon_sign"])
    for p in chart.get("planets", []) or []:
        if p.get("name") == "Moon":
            return SIGNS.index(p["sign"])
    raise ValueError("chart is missing the Moon's sign")


def _moon_nakshatra_index(chart: dict) -> int:
    return int(_moon_longitude(chart) // NAK_SPAN) % 27


# ── 1. Varna (0..1) ─────────────────────────────────────────────

VARNA_RANK = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1, "Mleccha": 0,
              "Servant": 1, "Butcher": 0}


def varna_score(boy: dict, girl: dict) -> int:
    bn = NAKSHATRAS[_moon_nakshatra_index(boy)]
    gn = NAKSHATRAS[_moon_nakshatra_index(girl)]
    bv = VARNA_RANK.get(NAKSHATRA_TABLE[bn]["varna"], 0)
    gv = VARNA_RANK.get(NAKSHATRA_TABLE[gn]["varna"], 0)
    return 1 if bv >= gv else 0


# ── 2. Vashya (0..2) ────────────────────────────────────────────

# Sign → vashya group
VASHYA_GROUP: dict[str, str] = {
    "Aries": "Chatushpada", "Taurus": "Chatushpada", "Gemini": "Manava",
    "Cancer": "Jalachara", "Leo": "Vanachara", "Virgo": "Manava",
    "Libra": "Manava", "Scorpio": "Keeta", "Sagittarius": "Manava",
    "Capricorn": "Jalachara", "Aquarius": "Manava", "Pisces": "Jalachara",
}


def vashya_score(boy: dict, girl: dict) -> int:
    bg = VASHYA_GROUP[SIGNS[_moon_sign_index(boy)]]
    gg = VASHYA_GROUP[SIGNS[_moon_sign_index(girl)]]
    if bg == gg:
        return 2
    # Compatible groups receive 1
    compat = {("Manava", "Vanachara"), ("Vanachara", "Manava"),
              ("Jalachara", "Keeta"), ("Keeta", "Jalachara")}
    if (bg, gg) in compat:
        return 1
    return 0


# ── 3. Tara (0..3) ──────────────────────────────────────────────


def tara_score(boy: dict, girl: dict) -> int:
    bn = _moon_nakshatra_index(boy)
    gn = _moon_nakshatra_index(girl)
    diff_bg = (gn - bn) % 9
    diff_gb = (bn - gn) % 9
    # Auspicious tara remainders: 0, 2, 4, 6, 8 → tara 1,3,5,7,9 (1-indexed)
    auspicious = {0, 2, 4, 6, 8}
    score = 0
    if diff_bg in auspicious:
        score += 1.5
    if diff_gb in auspicious:
        score += 1.5
    return int(score)


# ── 4. Yoni (0..4) ──────────────────────────────────────────────

YONI_TABLE = {
    "Horse": ("Buffalo", 1),
    "Elephant": ("Lion", 2),
    "Sheep": ("Monkey", 1),
    "Serpent": ("Mongoose", 4),
    "Dog": ("Deer", 3),
    "Cat": ("Rat", 4),
    "Rat": ("Cat", 4),
    "Cow": ("Tiger", 4),
    "Buffalo": ("Horse", 1),
    "Tiger": ("Cow", 4),
    "Deer": ("Dog", 3),
    "Monkey": ("Sheep", 1),
    "Mongoose": ("Serpent", 4),
    "Lion": ("Elephant", 2),
}


def yoni_score(boy: dict, girl: dict) -> int:
    bn = NAKSHATRAS[_moon_nakshatra_index(boy)]
    gn = NAKSHATRAS[_moon_nakshatra_index(girl)]
    by = NAKSHATRA_TABLE[bn]["yoni"]
    gy = NAKSHATRA_TABLE[gn]["yoni"]
    if by == gy:
        return 4
    enemy = YONI_TABLE.get(by)
    if enemy and enemy[0] == gy:
        return enemy[1]
    return 3


# ── 5. Graha Maitri (0..5) ──────────────────────────────────────

# Lord-of-sign for moon-sign rashi
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

FRIENDSHIP = {
    "Sun":     {"friend": {"Moon", "Mars", "Jupiter"}, "enemy": {"Venus", "Saturn"}},
    "Moon":    {"friend": {"Sun", "Mercury"}, "enemy": set()},
    "Mars":    {"friend": {"Sun", "Moon", "Jupiter"}, "enemy": {"Mercury"}},
    "Mercury": {"friend": {"Sun", "Venus"}, "enemy": {"Moon"}},
    "Jupiter": {"friend": {"Sun", "Moon", "Mars"}, "enemy": {"Mercury", "Venus"}},
    "Venus":   {"friend": {"Mercury", "Saturn"}, "enemy": {"Sun", "Moon"}},
    "Saturn":  {"friend": {"Mercury", "Venus"}, "enemy": {"Sun", "Moon", "Mars"}},
}


def _friendship_status(a: str, b: str) -> str:
    if a == b:
        return "self"
    if b in FRIENDSHIP.get(a, {}).get("friend", set()):
        return "friend"
    if b in FRIENDSHIP.get(a, {}).get("enemy", set()):
        return "enemy"
    return "neutral"


def graha_maitri_score(boy: dict, girl: dict) -> int:
    bl = SIGN_LORDS[SIGNS[_moon_sign_index(boy)]]
    gl = SIGN_LORDS[SIGNS[_moon_sign_index(girl)]]
    s_bg = _friendship_status(bl, gl)
    s_gb = _friendship_status(gl, bl)
    table = {("friend", "friend"): 5, ("friend", "neutral"): 4, ("neutral", "friend"): 4,
             ("neutral", "neutral"): 3, ("friend", "enemy"): 1, ("enemy", "friend"): 1,
             ("neutral", "enemy"): 0, ("enemy", "neutral"): 0, ("enemy", "enemy"): 0,
             ("self", "self"): 5, ("self", "friend"): 5, ("friend", "self"): 5,
             ("self", "neutral"): 4, ("neutral", "self"): 4,
             ("self", "enemy"): 0, ("enemy", "self"): 0}
    return table.get((s_bg, s_gb), 3)


# ── 6. Gana (0..6) ──────────────────────────────────────────────

GANA_MATRIX = {
    ("Deva", "Deva"): 6, ("Manushya", "Manushya"): 6, ("Rakshasa", "Rakshasa"): 6,
    ("Deva", "Manushya"): 5, ("Manushya", "Deva"): 5,
    ("Manushya", "Rakshasa"): 0, ("Rakshasa", "Manushya"): 1,
    ("Deva", "Rakshasa"): 1, ("Rakshasa", "Deva"): 0,
}


def gana_score(boy: dict, girl: dict) -> int:
    bg = NAKSHATRA_TABLE[NAKSHATRAS[_moon_nakshatra_index(boy)]]["gana"]
    gg = NAKSHATRA_TABLE[NAKSHATRAS[_moon_nakshatra_index(girl)]]["gana"]
    return GANA_MATRIX.get((bg, gg), 0)


# ── 7. Bhakoot (0..7) ───────────────────────────────────────────

# Bhakoot: based on offset between moon signs.
# Auspicious offsets (mod 12): 3, 4, 7, 10, 11 are inauspicious (dosha).


def bhakoot_score(boy: dict, girl: dict) -> int:
    bs = _moon_sign_index(boy)
    gs = _moon_sign_index(girl)
    diff_bg = (gs - bs) % 12
    diff_gb = (bs - gs) % 12
    bad = {1, 2, 5, 6, 8, 9}  # 6/8, 2/12, 5/9, 9/5
    if (diff_bg, diff_gb) in {(5, 7), (7, 5), (1, 11), (11, 1), (2, 10), (10, 2)}:
        # Some are partially bad
        return 0
    if diff_bg in bad or diff_gb in bad:
        return 0
    return 7


# ── 8. Nadi (0..8) ──────────────────────────────────────────────


def nadi_score(boy: dict, girl: dict) -> int:
    bn = NAKSHATRA_TABLE[NAKSHATRAS[_moon_nakshatra_index(boy)]]["nadi"]
    gn = NAKSHATRA_TABLE[NAKSHATRAS[_moon_nakshatra_index(girl)]]["nadi"]
    return 0 if bn == gn else 8


# ── Mangal Dosha ────────────────────────────────────────────────

MANGAL_DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}


def _mars_house(chart: dict) -> int | None:
    for p in chart.get("planets", []) or []:
        if p.get("name") == "Mars":
            return int(p.get("house", 0)) or None
    return None


def _mangal_dosha(chart: dict) -> dict:
    house = _mars_house(chart)
    present = bool(house and house in MANGAL_DOSHA_HOUSES)
    # Cancellation: Mars in own/exalted sign or Saturn/Mars in same house
    cancelled = False
    if present:
        for p in chart.get("planets", []) or []:
            if p.get("name") == "Mars" and p.get("sign") in {"Aries", "Scorpio", "Capricorn"}:
                cancelled = True
    return {
        "present": present,
        "houses_affected": [house] if present and house else [],
        "cancelled": cancelled,
    }


# ── Public API ──────────────────────────────────────────────────


def kundali_milan(boy_chart: dict, girl_chart: dict) -> dict:
    scores = {
        "varna": varna_score(boy_chart, girl_chart),
        "vashya": vashya_score(boy_chart, girl_chart),
        "tara": tara_score(boy_chart, girl_chart),
        "yoni": yoni_score(boy_chart, girl_chart),
        "graha_maitri": graha_maitri_score(boy_chart, girl_chart),
        "gana": gana_score(boy_chart, girl_chart),
        "bhakoot": bhakoot_score(boy_chart, girl_chart),
        "nadi": nadi_score(boy_chart, girl_chart),
    }
    total = sum(scores.values())
    if total >= 28:
        verdict = "excellent"
    elif total >= 24:
        verdict = "good"
    elif total >= 18:
        verdict = "average"
    else:
        verdict = "low"

    boy_md = _mangal_dosha(boy_chart)
    girl_md = _mangal_dosha(girl_chart)
    if boy_md["present"] and girl_md["present"]:
        match = "both"
    elif boy_md["present"] or girl_md["present"]:
        match = "one_only"
    else:
        match = "neither"

    warnings: list[str] = []
    if scores["nadi"] == 0:
        warnings.append("Nadi dosha — same nadi between partners")
    if scores["bhakoot"] == 0:
        warnings.append("Bhakoot dosha — inauspicious sign offset")
    if scores["gana"] == 0:
        warnings.append("Gana dosha — incompatible temperaments")
    if (boy_md["present"] and not boy_md["cancelled"]) or (
        girl_md["present"] and not girl_md["cancelled"]
    ):
        warnings.append("Mangal Dosha present without cancellation")

    summary = (
        f"Ashtakoota total {total}/36 → {verdict}. "
        f"Mangal Dosha: {match}. "
        + (f"Warnings: {'; '.join(warnings)}." if warnings else "No major doshas.")
    )

    return {
        "scores": scores,
        "total": total,
        "verdict": verdict,
        "mangal_dosha": {
            "boy": boy_md,
            "girl": girl_md,
            "match": match,
        },
        "warnings": warnings,
        "summary": summary,
    }


__all__ = ["kundali_milan"]
