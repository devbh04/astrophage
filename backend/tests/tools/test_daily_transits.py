"""Tests for ``app.tools.daily_transits``.

Feature: astroagent-phase-2-6, Property 9: every transit entry carries both
current (from Swiss Ephemeris at ``as_of``) and natal positions, and
``activated_houses`` is a subset of ``[1..12]``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.tools.birth_chart import (
    NAKSHATRAS,
    NAKSHATRA_LORDS,
    SIGNS,
    compute_birth_chart,
)
from app.tools.daily_transits import GRAHA_ORDER, get_daily_transits


# ── Fixtures ───────────────────────────────────────────────────


# A fixed natal chart used by the example-based tests below.
FIXED_BIRTH = {
    "birth_date": "1995-05-12",
    "birth_time": "04:30:00",
    "lat": 18.5204,
    "lng": 73.8567,
    "timezone": "Asia/Kolkata",
}

# A fixed ``as_of`` instant in the future (deterministic transit snapshot).
FIXED_AS_OF = "2024-06-15T12:00:00+00:00"


@pytest.fixture(scope="module")
def fixed_natal_chart() -> dict:
    """Compute the Mumbai 1995-05-12 04:30 IST natal chart once per session."""
    return compute_birth_chart(**FIXED_BIRTH)


# ── Example-based unit tests ───────────────────────────────────


def test_all_nine_grahas_appear(fixed_natal_chart: dict) -> None:
    """The transits list covers every Vedic graha exactly once."""
    result = get_daily_transits(fixed_natal_chart, as_of=FIXED_AS_OF)
    names = [entry["planet"] for entry in result["transits"]]
    assert names == list(GRAHA_ORDER)
    assert set(names) == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    }


def test_each_entry_has_current_and_natal_block(fixed_natal_chart: dict) -> None:
    """Every transit entry exposes both current and natal positions."""
    result = get_daily_transits(fixed_natal_chart, as_of=FIXED_AS_OF)
    for entry in result["transits"]:
        # Current block (from ephemeris at as_of)
        assert entry["current_sign"] in SIGNS
        assert isinstance(entry["current_house_from_lagna"], int)
        assert 1 <= entry["current_house_from_lagna"] <= 12
        assert isinstance(entry["retrograde"], bool)
        # Natal block (read from the chart)
        assert entry["natal_sign"] in SIGNS
        assert isinstance(entry["natal_house"], int)
        assert 1 <= entry["natal_house"] <= 12
        # Aspects + interpretation
        assert isinstance(entry["aspects_natal"], list)
        for aspect in entry["aspects_natal"]:
            assert aspect["target"] in {p["name"] for p in fixed_natal_chart["planets"]}
            assert isinstance(aspect["type"], str)
            assert 0.0 <= float(aspect["strength"]) <= 1.0
        assert entry["intensity"] in {"high", "medium", "low"}
        assert isinstance(entry["interpretation"], str) and entry["interpretation"]


def test_activated_houses_subset_of_one_through_twelve(
    fixed_natal_chart: dict,
) -> None:
    """``activated_houses`` is always a subset of [1..12]."""
    result = get_daily_transits(fixed_natal_chart, as_of=FIXED_AS_OF)
    activated = result["activated_houses"]
    assert isinstance(activated, list)
    assert all(isinstance(h, int) for h in activated)
    assert set(activated).issubset(set(range(1, 13)))
    # Sorted with no duplicates
    assert activated == sorted(set(activated))
    # At least the 9 transiting planets' own houses contribute.
    assert len(activated) >= 1


def test_top_level_shape(fixed_natal_chart: dict) -> None:
    """The top-level dict matches the design contract."""
    result = get_daily_transits(fixed_natal_chart, as_of=FIXED_AS_OF)
    assert set(result.keys()) >= {"as_of", "transits", "activated_houses", "headline"}
    # ``as_of`` round-trips as ISO 8601 in UTC
    parsed = datetime.fromisoformat(result["as_of"])
    assert parsed.tzinfo is not None
    assert parsed == datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
    assert isinstance(result["headline"], str) and result["headline"]


def test_default_as_of_is_now(fixed_natal_chart: dict) -> None:
    """Omitting ``as_of`` defaults to ``now()`` rather than raising."""
    before = datetime.now(tz=timezone.utc)
    result = get_daily_transits(fixed_natal_chart)
    after = datetime.now(tz=timezone.utc)
    parsed = datetime.fromisoformat(result["as_of"])
    assert before <= parsed <= after


def test_z_suffix_is_accepted(fixed_natal_chart: dict) -> None:
    """ISO 8601 strings with a trailing ``Z`` parse to UTC."""
    result = get_daily_transits(fixed_natal_chart, as_of="2024-06-15T12:00:00Z")
    parsed = datetime.fromisoformat(result["as_of"])
    assert parsed == datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "bad_as_of",
    [
        "not-a-date",
        "2024-13-40",
        "12:00 IST",
        "",
        "   ",
        "2024/06/15",
    ],
)
def test_unparseable_as_of_raises_value_error(
    fixed_natal_chart: dict, bad_as_of: str
) -> None:
    """Unparseable ``as_of`` strings raise ``ValueError``."""
    with pytest.raises(ValueError):
        get_daily_transits(fixed_natal_chart, as_of=bad_as_of)


def test_invalid_natal_chart_raises_value_error() -> None:
    """A natal chart missing the required structure raises ``ValueError``."""
    with pytest.raises(ValueError):
        get_daily_transits({}, as_of=FIXED_AS_OF)
    with pytest.raises(ValueError):
        get_daily_transits(
            {"ascendant": {"sign": "Atlantis"}, "planets": []},
            as_of=FIXED_AS_OF,
        )


# ── Property-based test (Property 9) ───────────────────────────


def _synthesize_natal_chart(
    asc_sign_idx: int, planet_sign_indices: list[int]
) -> dict:
    """Build a minimal valid natal chart from sampled sign indices.

    Mirrors the shape produced by ``compute_birth_chart`` closely enough that
    ``get_daily_transits`` can read the natal block (sign + house). The
    Swiss-Ephemeris-derived current block is computed independently from
    ``as_of``, so synthetic natal data is sufficient for Property 9.
    """
    asc_sign = SIGNS[asc_sign_idx]
    planets = []
    for name, sign_idx in zip(GRAHA_ORDER, planet_sign_indices, strict=True):
        # House = (planet_sign - asc_sign) mod 12 + 1
        house = ((sign_idx - asc_sign_idx) % 12) + 1
        # Pick a deterministic nakshatra inside the sign for the natal block.
        # Each sign spans 30°; nakshatras span 13°20'; multiple may overlap.
        long_in_sign = 5.0  # arbitrary, anywhere in [0, 30)
        sidereal_long = sign_idx * 30 + long_in_sign
        nak_idx = min(int(sidereal_long / (360 / 27)), 26)
        planets.append({
            "name": name,
            "degree": round(long_in_sign, 4),
            "total_degree": round(sidereal_long, 4),
            "sign": SIGNS[sign_idx],
            "house": house,
            "retrograde": False,
            "nakshatra": NAKSHATRAS[nak_idx],
            "pada": 1,
            "nakshatra_lord": NAKSHATRA_LORDS[nak_idx],
        })
    moon = next(p for p in planets if p["name"] == "Moon")
    sun = next(p for p in planets if p["name"] == "Sun")
    return {
        "sun_sign": sun["sign"],
        "moon_sign": moon["sign"],
        "ascendant": {
            "degree": 0.0,
            "total_degree": float(asc_sign_idx * 30),
            "sign": asc_sign,
            "nakshatra": NAKSHATRAS[(asc_sign_idx * 30) // (360 // 27) % 27],
            "pada": 1,
            "nakshatra_lord": NAKSHATRA_LORDS[
                (asc_sign_idx * 30) // (360 // 27) % 27
            ],
        },
        "planets": planets,
        "house_cusps": [],
        "ayanamsa": "Lahiri",
        "birth_time_known": True,
    }


# Strategies: sample valid natal charts and ISO ``as_of`` instants.
sign_index_st = st.integers(min_value=0, max_value=11)
planet_signs_st = st.lists(sign_index_st, min_size=9, max_size=9)
natal_chart_st = st.builds(_synthesize_natal_chart, sign_index_st, planet_signs_st)

# Bound the date range to where Swiss Ephemeris built-in data is reliable.
as_of_dt_st = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2100, 12, 31, 23, 59, 59),
    timezones=st.just(timezone.utc),
)


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(natal_chart=natal_chart_st, as_of_dt=as_of_dt_st)
def test_property_9_current_and_natal_blocks_present(
    natal_chart: dict, as_of_dt: datetime
) -> None:
    """**Validates: Requirements 9.1**

    Property 9: For every valid natal chart and ``as_of`` ISO timestamp, every
    entry in ``transits`` carries a current block (sign + house, derived from
    ephemeris at ``as_of``) and a natal block (sign + house from the chart),
    and ``activated_houses`` is a subset of ``[1..12]``.
    """
    result = get_daily_transits(natal_chart, as_of=as_of_dt.isoformat())

    # All nine grahas appear, in canonical order.
    assert [e["planet"] for e in result["transits"]] == list(GRAHA_ORDER)

    natal_by_name = {p["name"]: p for p in natal_chart["planets"]}

    for entry in result["transits"]:
        # Current block, from ephemeris at as_of
        assert entry["current_sign"] in SIGNS
        assert 1 <= entry["current_house_from_lagna"] <= 12
        # Natal block, read from the synthesized chart
        natal = natal_by_name[entry["planet"]]
        assert entry["natal_sign"] == natal["sign"]
        assert entry["natal_house"] == natal["house"]

    # activated_houses ⊆ [1..12], deduplicated and sorted
    activated = result["activated_houses"]
    assert set(activated).issubset(set(range(1, 13)))
    assert activated == sorted(set(activated))
