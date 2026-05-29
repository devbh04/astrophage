"""
Janma Nakshatra deep-analysis tool.

Returns the static attributes of the Moon's birth nakshatra: pada, lord,
deity, symbol, gana, yoni, nadi, varna, tatva, lucky colors/numbers, and
compatible/incompatible nakshatras.
"""

from __future__ import annotations

from app.tools.dasha import NAKSHATRA_LORDS, NAK_SPAN

NAKSHATRAS: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


# Static deity, symbol, gana, yoni, nadi, varna, tatva tables
NAKSHATRA_TABLE: dict[str, dict] = {
    "Ashwini":          {"deity": "Ashwini Kumaras", "symbol": "Horse's Head",       "gana": "Deva",     "yoni": "Horse",     "nadi": "Adi",   "varna": "Vaishya",   "tatva": "Earth"},
    "Bharani":          {"deity": "Yama",            "symbol": "Yoni",                "gana": "Manushya", "yoni": "Elephant",  "nadi": "Madhya","varna": "Mleccha",   "tatva": "Earth"},
    "Krittika":         {"deity": "Agni",            "symbol": "Razor",               "gana": "Rakshasa", "yoni": "Sheep",     "nadi": "Antya", "varna": "Brahmin",   "tatva": "Earth"},
    "Rohini":           {"deity": "Brahma",          "symbol": "Cart / Chariot",      "gana": "Manushya", "yoni": "Serpent",   "nadi": "Antya", "varna": "Shudra",    "tatva": "Earth"},
    "Mrigashira":       {"deity": "Soma",            "symbol": "Deer's Head",         "gana": "Deva",     "yoni": "Serpent",   "nadi": "Madhya","varna": "Servant",   "tatva": "Earth"},
    "Ardra":            {"deity": "Rudra",           "symbol": "Teardrop",            "gana": "Manushya", "yoni": "Dog",       "nadi": "Adi",   "varna": "Butcher",   "tatva": "Water"},
    "Punarvasu":        {"deity": "Aditi",           "symbol": "Bow and Quiver",      "gana": "Deva",     "yoni": "Cat",       "nadi": "Adi",   "varna": "Vaishya",   "tatva": "Water"},
    "Pushya":           {"deity": "Brihaspati",      "symbol": "Cow's Udder",         "gana": "Deva",     "yoni": "Sheep",     "nadi": "Madhya","varna": "Kshatriya", "tatva": "Water"},
    "Ashlesha":         {"deity": "Nagas",           "symbol": "Coiled Serpent",      "gana": "Rakshasa", "yoni": "Cat",       "nadi": "Antya", "varna": "Mleccha",   "tatva": "Water"},
    "Magha":            {"deity": "Pitris",          "symbol": "Royal Throne",        "gana": "Rakshasa", "yoni": "Rat",       "nadi": "Antya", "varna": "Shudra",    "tatva": "Water"},
    "Purva Phalguni":   {"deity": "Bhaga",           "symbol": "Front of Bed",        "gana": "Manushya", "yoni": "Rat",       "nadi": "Madhya","varna": "Brahmin",   "tatva": "Water"},
    "Uttara Phalguni":  {"deity": "Aryaman",         "symbol": "Back of Bed",         "gana": "Manushya", "yoni": "Cow",       "nadi": "Adi",   "varna": "Kshatriya", "tatva": "Fire"},
    "Hasta":            {"deity": "Savitr",          "symbol": "Hand / Fist",         "gana": "Deva",     "yoni": "Buffalo",   "nadi": "Adi",   "varna": "Vaishya",   "tatva": "Fire"},
    "Chitra":           {"deity": "Tvashtar",        "symbol": "Bright Jewel",        "gana": "Rakshasa", "yoni": "Tiger",     "nadi": "Madhya","varna": "Servant",   "tatva": "Fire"},
    "Swati":            {"deity": "Vayu",            "symbol": "Coral / Sapling",     "gana": "Deva",     "yoni": "Buffalo",   "nadi": "Antya", "varna": "Butcher",   "tatva": "Fire"},
    "Vishakha":         {"deity": "Indra-Agni",      "symbol": "Triumphal Arch",      "gana": "Rakshasa", "yoni": "Tiger",     "nadi": "Antya", "varna": "Mleccha",   "tatva": "Fire"},
    "Anuradha":         {"deity": "Mitra",           "symbol": "Lotus",               "gana": "Deva",     "yoni": "Deer",      "nadi": "Madhya","varna": "Shudra",    "tatva": "Fire"},
    "Jyeshtha":         {"deity": "Indra",           "symbol": "Earring / Umbrella",  "gana": "Rakshasa", "yoni": "Deer",      "nadi": "Adi",   "varna": "Servant",   "tatva": "Air"},
    "Mula":             {"deity": "Niriti",         "symbol": "Tied Bundle of Roots","gana": "Rakshasa", "yoni": "Dog",       "nadi": "Adi",   "varna": "Butcher",   "tatva": "Air"},
    "Purva Ashadha":    {"deity": "Apas",            "symbol": "Fan / Winnowing Bask","gana": "Manushya", "yoni": "Monkey",    "nadi": "Madhya","varna": "Brahmin",   "tatva": "Air"},
    "Uttara Ashadha":   {"deity": "Vishvadevas",     "symbol": "Elephant Tusk",       "gana": "Manushya", "yoni": "Mongoose",  "nadi": "Antya", "varna": "Kshatriya", "tatva": "Air"},
    "Shravana":         {"deity": "Vishnu",          "symbol": "Ear / Three Footprints","gana":"Deva",   "yoni": "Monkey",    "nadi": "Antya", "varna": "Mleccha",   "tatva": "Air"},
    "Dhanishta":        {"deity": "Vasus",           "symbol": "Drum / Flute",        "gana": "Rakshasa", "yoni": "Lion",      "nadi": "Madhya","varna": "Servant",   "tatva": "Ether"},
    "Shatabhisha":      {"deity": "Varuna",          "symbol": "Empty Circle",        "gana": "Rakshasa", "yoni": "Horse",     "nadi": "Adi",   "varna": "Butcher",   "tatva": "Ether"},
    "Purva Bhadrapada": {"deity": "Aja Ekapada",     "symbol": "Sword / Front of Bier","gana": "Manushya","yoni": "Lion",      "nadi": "Adi",   "varna": "Brahmin",   "tatva": "Ether"},
    "Uttara Bhadrapada":{"deity": "Ahir Budhnya",    "symbol": "Twins / Back of Bier","gana": "Manushya", "yoni": "Cow",       "nadi": "Madhya","varna": "Kshatriya", "tatva": "Ether"},
    "Revati":           {"deity": "Pushan",          "symbol": "Fish / Drum",         "gana": "Deva",     "yoni": "Elephant",  "nadi": "Antya", "varna": "Shudra",    "tatva": "Ether"},
}


LUCKY_COLORS: dict[str, list[str]] = {
    "Ashwini": ["red", "deep red"],
    "Bharani": ["blood red", "black"],
    "Krittika": ["white", "red"],
    "Rohini": ["white", "yellow"],
    "Mrigashira": ["silver", "white"],
    "Ardra": ["green", "green-blue"],
    "Punarvasu": ["lead grey", "yellow"],
    "Pushya": ["red", "black"],
    "Ashlesha": ["red", "black"],
    "Magha": ["ivory", "cream"],
    "Purva Phalguni": ["light brown", "pink"],
    "Uttara Phalguni": ["bright blue"],
    "Hasta": ["light green", "deep green"],
    "Chitra": ["black", "burnt orange"],
    "Swati": ["black", "deep blue"],
    "Vishakha": ["golden"],
    "Anuradha": ["reddish brown"],
    "Jyeshtha": ["cream", "tan"],
    "Mula": ["yellow"],
    "Purva Ashadha": ["black"],
    "Uttara Ashadha": ["copper"],
    "Shravana": ["light blue"],
    "Dhanishta": ["silver grey"],
    "Shatabhisha": ["blue-green"],
    "Purva Bhadrapada": ["silver grey", "smoke"],
    "Uttara Bhadrapada": ["purple"],
    "Revati": ["brown"],
}


LUCKY_NUMBERS: dict[str, list[int]] = {
    "Ashwini": [7, 9],
    "Bharani": [9, 5],
    "Krittika": [1, 5],
    "Rohini": [2, 9],
    "Mrigashira": [9, 2],
    "Ardra": [4, 9],
    "Punarvasu": [3, 9],
    "Pushya": [3, 7],
    "Ashlesha": [4, 9],
    "Magha": [1, 5],
    "Purva Phalguni": [6, 5],
    "Uttara Phalguni": [1, 5],
    "Hasta": [2, 5],
    "Chitra": [9, 7],
    "Swati": [4, 5],
    "Vishakha": [3, 9],
    "Anuradha": [8, 7],
    "Jyeshtha": [3, 9],
    "Mula": [4, 9],
    "Purva Ashadha": [3, 7],
    "Uttara Ashadha": [3, 9],
    "Shravana": [2, 9],
    "Dhanishta": [9, 2],
    "Shatabhisha": [4, 9],
    "Purva Bhadrapada": [3, 9],
    "Uttara Bhadrapada": [8, 3],
    "Revati": [3, 5],
}


# Compatibility tables — derived from Gana / Nadi / Yoni pairings.
# Compatible nakshatras share the same gana and have non-clashing yoni / nadi.
def _compatibility(target: str) -> tuple[list[str], list[str]]:
    target_attrs = NAKSHATRA_TABLE[target]
    compatible: list[str] = []
    incompatible: list[str] = []
    for nak in NAKSHATRAS:
        if nak == target:
            continue
        attrs = NAKSHATRA_TABLE[nak]
        same_gana = attrs["gana"] == target_attrs["gana"]
        same_nadi = attrs["nadi"] == target_attrs["nadi"]
        same_yoni = attrs["yoni"] == target_attrs["yoni"]
        if same_gana and not same_nadi:
            compatible.append(nak)
        elif same_nadi and not same_gana:
            incompatible.append(nak)
        elif same_yoni and not same_gana:
            incompatible.append(nak)
    return compatible[:9], incompatible[:9]


def _moon_longitude(natal_chart: dict) -> float:
    """Extract the Moon's sidereal longitude from a chart dict."""
    if "moon_longitude" in natal_chart:
        return float(natal_chart["moon_longitude"])
    for planet in natal_chart.get("planets", []) or []:
        if planet.get("name") == "Moon":
            if "total_degree" in planet:
                return float(planet["total_degree"])
    raise ValueError("natal_chart is missing the Moon's longitude")


def compute_nakshatra_details(natal_chart: dict) -> dict:
    """Return a deep-analysis dict for the Moon's birth nakshatra."""
    moon_long = _moon_longitude(natal_chart)
    nak_index = int(moon_long // NAK_SPAN)
    nak_index = min(nak_index, 26)
    pada_span = NAK_SPAN / 4.0
    pos_in_nak = moon_long - nak_index * NAK_SPAN
    pada = int(pos_in_nak // pada_span) + 1
    pada = max(1, min(pada, 4))

    nak_name = NAKSHATRAS[nak_index]
    lord = NAKSHATRA_LORDS[nak_index]
    static = NAKSHATRA_TABLE[nak_name]
    compatible, incompatible = _compatibility(nak_name)

    return {
        "janma_nakshatra": nak_name,
        "pada": pada,
        "lord": lord,
        "deity": static["deity"],
        "symbol": static["symbol"],
        "gana": static["gana"],
        "yoni": static["yoni"],
        "nadi": static["nadi"],
        "varna": static["varna"],
        "tatva": static["tatva"],
        "lucky_colors": list(LUCKY_COLORS.get(nak_name, [])),
        "lucky_numbers": list(LUCKY_NUMBERS.get(nak_name, [])),
        "compatible_nakshatras": compatible,
        "incompatible_nakshatras": incompatible,
    }


__all__ = [
    "compute_nakshatra_details",
    "NAKSHATRAS",
    "NAKSHATRA_TABLE",
    "LUCKY_COLORS",
    "LUCKY_NUMBERS",
]
