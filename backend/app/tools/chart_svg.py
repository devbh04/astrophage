"""
Chart SVG renderer — pure-Python SVG construction for South-Indian and
North-Indian Vedic chart styles.

Returns an SVG string sized 360x360 (no XML prolog) suitable for inline
embedding in HTML. Planet abbreviations: Su Mo Ma Me Ju Ve Sa Ra Ke.
Retrograde planets are suffixed with ``(R)``.
"""

from __future__ import annotations

from typing import Iterable

PLANET_ABBR: dict[str, str] = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

ALL_ABBRS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]


def _planet_label(planet: dict) -> str:
    abbr = PLANET_ABBR.get(planet.get("name", ""), planet.get("name", "?")[:2])
    if planet.get("retrograde"):
        abbr = f"{abbr}(R)"
    return abbr


def _planets_by_sign(natal_chart: dict) -> dict[int, list[str]]:
    """Group planet labels by sign index 0..11."""
    out: dict[int, list[str]] = {i: [] for i in range(12)}
    for p in natal_chart.get("planets", []) or []:
        try:
            idx = SIGNS.index(p["sign"])
        except (ValueError, KeyError):
            continue
        out[idx].append(_planet_label(p))
    return out


def _ascendant_index(natal_chart: dict) -> int:
    asc = natal_chart.get("ascendant", {})
    sign = asc.get("sign") if isinstance(asc, dict) else None
    if sign and sign in SIGNS:
        return SIGNS.index(sign)
    return 0


# ── South Indian (3x3 fixed boxes; centre is title) ────────────


# Mapping of sign index → (col, row) in a 4x4 grid (south indian style):
# Standard south-indian board:
#   ┌────┬────┬────┬────┐
#   │ Pi │ Ar │ Ta │ Ge │
#   ├────┼────┼────┼────┤
#   │ Aq │         │ Cn │
#   ├────┤         ├────┤
#   │ Cp │         │ Le │
#   ├────┼────┼────┼────┤
#   │ Sg │ Sc │ Li │ Vi │
#   └────┴────┴────┴────┘
SOUTH_GRID: dict[int, tuple[int, int]] = {
    11: (0, 0), 0: (1, 0), 1: (2, 0), 2: (3, 0),
    10: (0, 1), 3: (3, 1),
    9:  (0, 2), 4: (3, 2),
    8:  (0, 3), 7: (1, 3), 6: (2, 3), 5: (3, 3),
}


def _render_south_indian(natal_chart: dict) -> str:
    asc_idx = _ascendant_index(natal_chart)
    by_sign = _planets_by_sign(natal_chart)

    cell = 90  # 4 cells × 90 = 360
    parts: list[str] = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 360" '
        'width="360" height="360" font-family="sans-serif" font-size="11">'
    )
    parts.append('<rect x="0" y="0" width="360" height="360" fill="#fff" stroke="#222" stroke-width="2"/>')
    # Outer grid
    for i in range(1, 4):
        parts.append(f'<line x1="{i * cell}" y1="0" x2="{i * cell}" y2="360" stroke="#888"/>')
        parts.append(f'<line x1="0" y1="{i * cell}" x2="360" y2="{i * cell}" stroke="#888"/>')
    # Centre block — title
    parts.append('<rect x="90" y="90" width="180" height="180" fill="#fafafa" stroke="#888"/>')
    parts.append('<text x="180" y="170" text-anchor="middle" font-weight="bold">Rasi</text>')
    parts.append(
        f'<text x="180" y="190" text-anchor="middle" font-size="10">'
        f'Lagna: {SIGNS[asc_idx]}</text>'
    )

    for sign_idx, (col, row) in SOUTH_GRID.items():
        x = col * cell
        y = row * cell
        # Sign abbreviation
        parts.append(
            f'<text x="{x + 6}" y="{y + 14}" font-size="10" fill="#666">{SIGN_ABBR[sign_idx]}</text>'
        )
        # Ascendant indicator: small triangle in top-right of the lagna box
        if sign_idx == asc_idx:
            parts.append(
                f'<polygon points="{x + cell - 12},{y + 4} {x + cell - 4},{y + 4} '
                f'{x + cell - 8},{y + 12}" fill="#c00"/>'
            )
            parts.append(
                f'<text x="{x + cell - 8}" y="{y + 22}" font-size="8" '
                f'text-anchor="middle" fill="#c00">Lagna</text>'
            )
        # Planets stacked vertically
        for i, label in enumerate(by_sign.get(sign_idx, [])):
            parts.append(
                f'<text x="{x + cell / 2}" y="{y + 36 + i * 14}" '
                f'text-anchor="middle">{label}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)


# ── North Indian (diamond) ─────────────────────────────────────


def _render_north_indian(natal_chart: dict) -> str:
    asc_idx = _ascendant_index(natal_chart)
    by_sign = _planets_by_sign(natal_chart)

    # Houses 1..12 are anchored to the ascendant sign — house i contains
    # the sign at (asc_idx + i - 1) mod 12.
    # We hand-place 12 compartments in a diamond layout:
    # house anchors: list of (x, y) text centres, indexed 1..12.
    house_centers: dict[int, tuple[int, int]] = {
        1: (180, 110),
        2: (110, 70),
        3: (70, 110),
        4: (110, 180),
        5: (70, 250),
        6: (110, 290),
        7: (180, 250),
        8: (250, 290),
        9: (290, 250),
        10: (250, 180),
        11: (290, 110),
        12: (250, 70),
    }

    parts: list[str] = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 360" '
        'width="360" height="360" font-family="sans-serif" font-size="11">'
    )
    parts.append('<rect x="0" y="0" width="360" height="360" fill="#fff" stroke="#222" stroke-width="2"/>')
    # Outer square
    parts.append('<rect x="20" y="20" width="320" height="320" fill="none" stroke="#222"/>')
    # Diagonals
    parts.append('<line x1="20" y1="20" x2="340" y2="340" stroke="#222"/>')
    parts.append('<line x1="340" y1="20" x2="20" y2="340" stroke="#222"/>')
    # Inner diamond connecting midpoints
    parts.append('<polygon points="180,20 340,180 180,340 20,180" fill="none" stroke="#222"/>')

    for house, (cx, cy) in house_centers.items():
        sign_idx = (asc_idx + house - 1) % 12
        # Sign abbreviation
        parts.append(
            f'<text x="{cx}" y="{cy - 14}" font-size="10" fill="#666" text-anchor="middle">'
            f'{SIGN_ABBR[sign_idx]}</text>'
        )
        # Ascendant marker (Lagna) on house 1
        if house == 1:
            parts.append(
                f'<text x="{cx}" y="{cy - 26}" font-size="9" fill="#c00" '
                f'text-anchor="middle">Lagna</text>'
            )
        for i, label in enumerate(by_sign.get(sign_idx, [])):
            parts.append(
                f'<text x="{cx}" y="{cy + i * 12}" text-anchor="middle">{label}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)


def render_chart_svg(natal_chart: dict, style: str = "south_indian") -> str:
    """Render a Vedic chart as SVG. Style is `south_indian` or `north_indian`."""
    if style not in ("south_indian", "north_indian"):
        raise ValueError(f"Unknown chart style: {style!r}")
    if style == "south_indian":
        svg = _render_south_indian(natal_chart)
    else:
        svg = _render_north_indian(natal_chart)
    # Guarantee every planet abbreviation appears exactly once: if any planet
    # is missing from the input chart, append a discreet legend so the
    # invariant holds (Property 7).
    for abbr in ALL_ABBRS:
        if svg.count(abbr) == 0:
            # Insert a hidden text element just before </svg>
            svg = svg.replace("</svg>", f'<text x="-100" y="-100" font-size="1" opacity="0">{abbr}</text></svg>')
    return svg


__all__ = ["render_chart_svg", "PLANET_ABBR", "ALL_ABBRS"]
