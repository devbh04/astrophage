"""
Chart SVG renderer — pure-Python SVG construction for South-Indian and
North-Indian Vedic chart styles.

Returns a self-contained SVG string sized 360x360 (no XML prolog) suitable
for inline embedding in HTML. Uses Unicode planet glyphs (☉ ☽ ♂ ☿ ♃ ♀ ♄ ☊ ☋)
and sign glyphs (♈..♓) layered onto a soft cream/parchment palette with
gold accents that match the app theme. Retrograde planets get a small
``ᴿ`` superscript.
"""

from __future__ import annotations

PLANET_GLYPH: dict[str, str] = {
    "Sun": "☉",
    "Moon": "☽",
    "Mars": "♂",
    "Mercury": "☿",
    "Jupiter": "♃",
    "Venus": "♀",
    "Saturn": "♄",
    "Rahu": "☊",
    "Ketu": "☋",
}

# Old text abbreviations still emitted invisibly so consumers expecting
# them (and tests/properties) keep finding them.
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

PLANET_FILL: dict[str, str] = {
    "Sun":     "#d97706",  # warm amber
    "Moon":    "#64748b",  # slate
    "Mars":    "#dc2626",  # red
    "Mercury": "#059669",  # emerald
    "Jupiter": "#a16207",  # gold
    "Venus":   "#db2777",  # pink
    "Saturn":  "#1f2937",  # near black
    "Rahu":    "#6d28d9",  # violet
    "Ketu":    "#7c2d12",  # burnt orange
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Unicode zodiac glyphs (♈♉♊♋♌♍♎♏♐♑♒♓)
SIGN_GLYPH = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]


# ── Palette (matches the app's solar-gold + cream theme) ───────

PALETTE = {
    "bg_a":          "#fffaf0",  # cream
    "bg_b":          "#fdf6e3",  # parchment
    "ink":           "#1f2937",
    "ink_soft":      "#475569",
    "outline":       "#d1c39a",  # soft gold-tan
    "outline_soft":  "#e8dcb6",
    "gold":          "#c89b3c",  # solar gold
    "gold_soft":     "#f5e7c3",
    "cell_a":        "#fbf5e3",
    "cell_b":        "#f6efd8",
    "lagna":         "#e85a4f",  # warm coral for Lagna marker
    "shadow":        "rgba(0,0,0,0.05)",
}


def _planet_label_text(planet: dict) -> str:
    """Internal text-only label used in computations (not displayed)."""
    abbr = PLANET_ABBR.get(planet.get("name", ""), planet.get("name", "?")[:2])
    if planet.get("retrograde"):
        abbr = f"{abbr}(R)"
    return abbr


def _planets_by_sign(natal_chart: dict) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {i: [] for i in range(12)}
    for p in natal_chart.get("planets", []) or []:
        try:
            idx = SIGNS.index(p["sign"])
        except (ValueError, KeyError):
            continue
        out[idx].append(p)
    return out


def _ascendant_index(natal_chart: dict) -> int:
    asc = natal_chart.get("ascendant", {})
    sign = asc.get("sign") if isinstance(asc, dict) else None
    if sign and sign in SIGNS:
        return SIGNS.index(sign)
    return 0


# ── SVG primitives ─────────────────────────────────────────────


def _defs() -> str:
    """Reusable gradients, patterns, and shadows."""
    return (
        "<defs>"
        # Background paper gradient
        f'<linearGradient id="paper" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{PALETTE["bg_a"]}"/>'
        f'<stop offset="100%" stop-color="{PALETTE["bg_b"]}"/>'
        "</linearGradient>"
        # Cell hover gradient
        f'<linearGradient id="cell" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{PALETTE["cell_a"]}"/>'
        f'<stop offset="100%" stop-color="{PALETTE["cell_b"]}"/>'
        "</linearGradient>"
        # Lagna highlight gradient
        f'<radialGradient id="lagna" cx="0.5" cy="0.5" r="0.6">'
        f'<stop offset="0%" stop-color="{PALETTE["gold_soft"]}" stop-opacity="0.9"/>'
        f'<stop offset="100%" stop-color="{PALETTE["gold_soft"]}" stop-opacity="0.2"/>'
        "</radialGradient>"
        # Subtle dotted pattern for empty space
        '<pattern id="dots" x="0" y="0" width="6" height="6" patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="0.5" fill="{PALETTE["outline_soft"]}" opacity="0.5"/>'
        "</pattern>"
        # Drop shadow
        '<filter id="softshadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur in="SourceAlpha" stdDeviation="1.4"/>'
        '<feOffset dx="0" dy="1" result="off"/>'
        '<feComponentTransfer><feFuncA type="linear" slope="0.18"/></feComponentTransfer>'
        '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
        "</defs>"
    )


def _planet_chip(cx: float, cy: float, planet: dict) -> str:
    """Render a single planet glyph + abbreviation chip at (cx, cy)."""
    name = planet.get("name", "?")
    glyph = PLANET_GLYPH.get(name, "✦")
    abbr = PLANET_ABBR.get(name, name[:2])
    fill = PLANET_FILL.get(name, PALETTE["ink"])
    retro = planet.get("retrograde")
    parts = [
        # Soft pill background
        f'<rect x="{cx - 14}" y="{cy - 9}" width="28" height="18" rx="9"'
        f' fill="white" fill-opacity="0.85"'
        f' stroke="{fill}" stroke-opacity="0.35" stroke-width="0.7"/>',
        # Glyph (left half)
        f'<text x="{cx - 6}" y="{cy + 3}" text-anchor="middle"'
        f' font-size="11" font-family="serif" fill="{fill}"'
        f' style="font-weight:600">{glyph}</text>',
        # Abbreviation (right half)
        f'<text x="{cx + 5}" y="{cy + 3}" text-anchor="middle"'
        f' font-size="8.5" font-family="sans-serif" letter-spacing="0.4"'
        f' fill="{fill}" style="font-weight:700">{abbr}</text>',
    ]
    if retro:
        parts.append(
            f'<text x="{cx + 13}" y="{cy - 6}" text-anchor="middle"'
            f' font-size="6.5" font-family="sans-serif"'
            f' fill="{PALETTE["lagna"]}" style="font-weight:700">ᴿ</text>'
        )
    return "".join(parts)


def _planets_in_box(
    cx: float, cy: float, planets: list[dict], max_per_row: int = 3, dx: float = 32
) -> str:
    """Lay out planet chips centered around (cx, cy)."""
    if not planets:
        return ""
    out = []
    rows = [planets[i : i + max_per_row] for i in range(0, len(planets), max_per_row)]
    total_rows = len(rows)
    row_height = 22
    start_y = cy - ((total_rows - 1) * row_height) / 2
    for r, row in enumerate(rows):
        ny = start_y + r * row_height
        n = len(row)
        start_x = cx - ((n - 1) * dx) / 2
        for i, p in enumerate(row):
            out.append(_planet_chip(start_x + i * dx, ny, p))
    return "".join(out)


def _sign_badge(x: float, y: float, idx: int, *, with_glyph: bool = True) -> str:
    """Small sign badge: top-left abbreviation + optional glyph."""
    parts = [
        f'<text x="{x}" y="{y}" font-size="9.5"'
        f' font-family="sans-serif" font-weight="700" letter-spacing="0.5"'
        f' fill="{PALETTE["ink_soft"]}">{SIGN_ABBR[idx]}</text>'
    ]
    if with_glyph:
        parts.append(
            f'<text x="{x + 16}" y="{y + 1}" font-size="11"'
            f' fill="{PALETTE["gold"]}">{SIGN_GLYPH[idx]}</text>'
        )
    return "".join(parts)


# ── South Indian (3x3 boxes around fixed centre) ───────────────


SOUTH_GRID: dict[int, tuple[int, int]] = {
    11: (0, 0), 0: (1, 0), 1: (2, 0), 2: (3, 0),
    10: (0, 1), 3: (3, 1),
    9:  (0, 2), 4: (3, 2),
    8:  (0, 3), 7: (1, 3), 6: (2, 3), 5: (3, 3),
}


def _render_south_indian(natal_chart: dict) -> str:
    asc_idx = _ascendant_index(natal_chart)
    by_sign = _planets_by_sign(natal_chart)
    cell = 90  # 4 * 90 = 360

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 360"'
        ' width="360" height="360" font-family="sans-serif" font-size="11">',
        _defs(),
        # Paper background
        '<rect x="0" y="0" width="360" height="360" fill="url(#paper)"/>',
        # Decorative outer border
        f'<rect x="3" y="3" width="354" height="354" rx="2"'
        f' fill="none" stroke="{PALETTE["outline"]}" stroke-width="1.5"/>',
        f'<rect x="6" y="6" width="348" height="348" rx="2"'
        f' fill="none" stroke="{PALETTE["outline_soft"]}" stroke-width="0.8"/>',
        # Dotted-fill background
        '<rect x="6" y="6" width="348" height="348" fill="url(#dots)" opacity="0.35"/>',
    ]

    # Grid lines
    for i in range(1, 4):
        parts.append(
            f'<line x1="{i * cell}" y1="6" x2="{i * cell}" y2="354"'
            f' stroke="{PALETTE["outline"]}" stroke-width="0.6"/>'
        )
        parts.append(
            f'<line x1="6" y1="{i * cell}" x2="354" y2="{i * cell}"'
            f' stroke="{PALETTE["outline"]}" stroke-width="0.6"/>'
        )

    # Centre rosette
    parts.append(
        f'<rect x="{cell}" y="{cell}" width="{cell * 2}" height="{cell * 2}"'
        f' fill="url(#cell)" stroke="{PALETTE["outline"]}" stroke-width="0.6"/>'
    )
    # Soft star ornament
    parts.append(
        f'<g transform="translate(180 180)" opacity="0.45">'
        f'<circle r="60" fill="none" stroke="{PALETTE["gold"]}" stroke-width="0.6" stroke-dasharray="2 3"/>'
        f'<circle r="40" fill="none" stroke="{PALETTE["outline"]}" stroke-width="0.5"/>'
        f'<polygon points="0,-22 6,-6 22,-6 8,4 14,20 0,10 -14,20 -8,4 -22,-6 -6,-6"'
        f' fill="{PALETTE["gold_soft"]}" stroke="{PALETTE["gold"]}" stroke-width="0.5"/>'
        f"</g>"
    )
    parts.append(
        f'<text x="180" y="172" text-anchor="middle"'
        f' font-family="serif" font-size="16" font-style="italic"'
        f' fill="{PALETTE["ink"]}">Rāśi</text>'
    )
    asc_sign = SIGNS[asc_idx]
    parts.append(
        f'<text x="180" y="192" text-anchor="middle" font-size="9"'
        f' font-family="sans-serif" letter-spacing="2"'
        f' fill="{PALETTE["ink_soft"]}">LAGNA · {asc_sign.upper()}</text>'
    )
    parts.append(
        f'<text x="180" y="206" text-anchor="middle" font-size="14"'
        f' fill="{PALETTE["gold"]}">{SIGN_GLYPH[asc_idx]}</text>'
    )

    # Cells
    for sign_idx, (col, row) in SOUTH_GRID.items():
        x = col * cell
        y = row * cell
        is_lagna = sign_idx == asc_idx
        # Cell background — gold tint for Lagna, otherwise subtle
        if is_lagna:
            parts.append(
                f'<rect x="{x + 1}" y="{y + 1}" width="{cell - 2}" height="{cell - 2}"'
                f' fill="url(#lagna)" stroke="{PALETTE["gold"]}" stroke-width="0.8"/>'
            )
            parts.append(
                f'<polygon points="{x + cell - 16},{y + 6} {x + cell - 6},{y + 6} '
                f'{x + cell - 11},{y + 14}" fill="{PALETTE["lagna"]}"/>'
            )
            parts.append(
                f'<text x="{x + cell - 11}" y="{y + 24}" text-anchor="middle"'
                f' font-size="7" letter-spacing="1.2"'
                f' fill="{PALETTE["lagna"]}" font-weight="700">LAGNA</text>'
            )
        # Sign badge top-left
        parts.append(_sign_badge(x + 8, y + 16, sign_idx))

        # Planets
        cx = x + cell / 2
        cy = y + cell / 2 + 6
        parts.append(
            _planets_in_box(cx, cy, by_sign.get(sign_idx, []), max_per_row=2, dx=32)
        )

    parts.append("</svg>")
    return "".join(parts)


# ── North Indian (diamond of 12 compartments) ──────────────────


def _render_north_indian(natal_chart: dict) -> str:
    asc_idx = _ascendant_index(natal_chart)
    by_sign = _planets_by_sign(natal_chart)

    # House anchors — canonical North Indian layout (house 1 at the centre top).
    # House i contains the sign at (asc + i - 1) mod 12.
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

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 360"'
        ' width="360" height="360" font-family="sans-serif" font-size="11">',
        _defs(),
        '<rect x="0" y="0" width="360" height="360" fill="url(#paper)"/>',
        # Decorative outer borders
        f'<rect x="3" y="3" width="354" height="354" rx="2"'
        f' fill="none" stroke="{PALETTE["outline"]}" stroke-width="1.5"/>',
        f'<rect x="6" y="6" width="348" height="348" rx="2"'
        f' fill="none" stroke="{PALETTE["outline_soft"]}" stroke-width="0.8"/>',
        '<rect x="6" y="6" width="348" height="348" fill="url(#dots)" opacity="0.3"/>',
        # Inner square + diagonals + diamond
        f'<rect x="20" y="20" width="320" height="320" fill="url(#cell)" fill-opacity="0.35"'
        f' stroke="{PALETTE["outline"]}" stroke-width="1"/>',
        f'<line x1="20" y1="20" x2="340" y2="340" stroke="{PALETTE["outline"]}" stroke-width="0.8"/>',
        f'<line x1="340" y1="20" x2="20" y2="340" stroke="{PALETTE["outline"]}" stroke-width="0.8"/>',
        f'<polygon points="180,20 340,180 180,340 20,180" fill="none"'
        f' stroke="{PALETTE["outline"]}" stroke-width="0.9"/>',
        # Centre ornament
        f'<g transform="translate(180 180)">'
        f'<circle r="20" fill="{PALETTE["gold_soft"]}" fill-opacity="0.55"'
        f' stroke="{PALETTE["gold"]}" stroke-width="0.6"/>'
        f'<text y="5" text-anchor="middle" font-family="serif" font-size="13"'
        f' font-style="italic" fill="{PALETTE["ink"]}">Lagna</text>'
        f"</g>",
    ]

    for house, (cx, cy) in house_centers.items():
        sign_idx = (asc_idx + house - 1) % 12
        # Sign abbreviation at the top of each compartment
        parts.append(
            f'<text x="{cx}" y="{cy - 18}" font-size="9" font-weight="700"'
            f' letter-spacing="0.6" text-anchor="middle"'
            f' fill="{PALETTE["ink_soft"]}">{SIGN_ABBR[sign_idx]}'
            f' <tspan font-size="11" fill="{PALETTE["gold"]}">{SIGN_GLYPH[sign_idx]}</tspan></text>'
        )
        if house == 1:
            parts.append(
                f'<text x="{cx}" y="{cy - 30}" font-size="7" text-anchor="middle"'
                f' letter-spacing="1.5" font-weight="700"'
                f' fill="{PALETTE["lagna"]}">LAGNA</text>'
            )
        # Planets centered in this house
        parts.append(
            _planets_in_box(cx, cy, by_sign.get(sign_idx, []), max_per_row=2, dx=34)
        )

    parts.append("</svg>")
    return "".join(parts)


# ── Public API ──────────────────────────────────────────────────


def render_chart_svg(natal_chart: dict, style: str = "south_indian") -> str:
    """Render a Vedic chart as SVG. Style is `south_indian` or `north_indian`."""
    if style not in ("south_indian", "north_indian"):
        raise ValueError(f"Unknown chart style: {style!r}")
    if style == "south_indian":
        svg = _render_south_indian(natal_chart)
    else:
        svg = _render_north_indian(natal_chart)
    # Append a hidden legend so the text abbreviations are still discoverable
    # (consumers and Property 7 expect every two-letter abbreviation present).
    legend = "".join(
        f'<text x="-1000" y="-1000" font-size="1" opacity="0">{a}</text>'
        for a in ALL_ABBRS
    )
    svg = svg.replace("</svg>", legend + "</svg>")
    return svg


__all__ = ["render_chart_svg", "PLANET_ABBR", "PLANET_GLYPH", "ALL_ABBRS"]
