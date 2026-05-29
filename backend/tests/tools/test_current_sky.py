"""Unit tests for ``app.tools.current_sky.get_current_sky``.

Covers the design §2.5 contract:

- A fixed ``as_of`` (deterministic Swiss Ephemeris) returns all nine grahas
  with ``sign`` / ``degree`` / ``retrograde`` / ``nakshatra``.
- ``moon_phase.illumination`` lies in ``[0, 1]`` and the lunar-event ISO
  timestamps land strictly after ``as_of``.
- An unparseable ``as_of`` raises ``ValueError`` (Requirement 9.4).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.tools.birth_chart import NAKSHATRAS, SIGNS
from app.tools.current_sky import GRAHA_ORDER, get_current_sky


# A stable timestamp (2024-06-15 12:00 UTC) chosen so:
#   - both lunar nodes are retrograde (Rahu/Ketu always),
#   - the Moon is mid-cycle (good illumination coverage),
#   - the next-sign-change look-ahead succeeds well within the window.
FIXED_AS_OF = "2024-06-15T12:00:00Z"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_iso(s: str) -> datetime:
    """Parse an ISO 8601 string (with optional ``Z``) to an aware datetime."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ── Structural / contract tests ──────────────────────────────────────────────


def test_returns_top_level_keys() -> None:
    """All design §2.5 top-level keys are present."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    expected_keys = {
        "as_of",
        "planets",
        "moon_phase",
        "retrogrades",
        "next_sign_change",
        "next_event",
    }
    assert expected_keys.issubset(result.keys())


def test_as_of_is_echoed_in_utc_iso() -> None:
    """The returned ``as_of`` is the canonical UTC form of the input."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    assert result["as_of"] == FIXED_AS_OF


def test_as_of_defaults_to_now_when_omitted() -> None:
    """Omitting ``as_of`` uses "now" (UTC) and still returns a valid snapshot."""
    before = datetime.now(tz=timezone.utc)
    result = get_current_sky()
    after = datetime.now(tz=timezone.utc)

    parsed = _parse_iso(result["as_of"])
    assert before <= parsed <= after
    assert len(result["planets"]) == 9


# ── Planets: nine grahas with required fields ────────────────────────────────


def test_planets_cover_all_nine_grahas_in_canonical_order() -> None:
    """All nine grahas appear exactly once in the canonical Vedic order."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    names = [p["name"] for p in result["planets"]]
    assert names == GRAHA_ORDER


def test_each_planet_has_required_fields_with_valid_values() -> None:
    """Every entry has ``sign`` / ``degree`` / ``retrograde`` / ``nakshatra``
    and each value is within its documented domain."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    valid_signs = set(SIGNS)
    valid_nakshatras = set(NAKSHATRAS)

    for entry in result["planets"]:
        # Required keys
        assert {"sign", "degree", "retrograde", "nakshatra"} <= entry.keys()
        # Sign is one of the 12 zodiac signs.
        assert entry["sign"] in valid_signs, entry
        # Degree is the position within the sign.
        assert isinstance(entry["degree"], (int, float))
        assert 0.0 <= float(entry["degree"]) < 30.0, entry
        # Retrograde is a real bool, not a truthy int.
        assert isinstance(entry["retrograde"], bool), entry
        # Nakshatra is one of the 27.
        assert entry["nakshatra"] in valid_nakshatras, entry


def test_rahu_and_ketu_are_always_retrograde() -> None:
    """The lunar nodes are conventionally retrograde in Vedic charts."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    by_name = {p["name"]: p for p in result["planets"]}
    assert by_name["Rahu"]["retrograde"] is True
    assert by_name["Ketu"]["retrograde"] is True


def test_rahu_and_ketu_are_exactly_180_degrees_apart() -> None:
    """Ketu is the south node — geometrically 180° from Rahu."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    by_name = {p["name"]: p for p in result["planets"]}
    rahu_sign_idx = SIGNS.index(by_name["Rahu"]["sign"])
    ketu_sign_idx = SIGNS.index(by_name["Ketu"]["sign"])
    assert (ketu_sign_idx - rahu_sign_idx) % 12 == 6


def test_retrogrades_list_matches_planet_flags() -> None:
    """The top-level ``retrogrades`` list is consistent with per-planet flags."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    flagged = [p["name"] for p in result["planets"] if p["retrograde"]]
    assert result["retrogrades"] == flagged
    # At minimum, both nodes should always be present.
    assert "Rahu" in result["retrogrades"]
    assert "Ketu" in result["retrogrades"]


# ── Moon phase ───────────────────────────────────────────────────────────────


def test_moon_phase_has_required_fields() -> None:
    result = get_current_sky(as_of=FIXED_AS_OF)
    moon_phase = result["moon_phase"]
    assert {"name", "illumination", "next_full_moon", "next_new_moon"} <= moon_phase.keys()


def test_moon_phase_illumination_within_unit_interval() -> None:
    """Requirement 9.3: ``moon_phase.illumination`` ∈ [0, 1]."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    illumination = result["moon_phase"]["illumination"]
    assert isinstance(illumination, (int, float))
    assert 0.0 <= float(illumination) <= 1.0


def test_moon_phase_name_is_one_of_eight_canonical_names() -> None:
    result = get_current_sky(as_of=FIXED_AS_OF)
    valid_names = {
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
    }
    assert result["moon_phase"]["name"] in valid_names


def test_next_full_and_new_moon_are_after_as_of_and_within_a_synodic_month() -> None:
    """Both lunar events are strictly after ``as_of`` and within ~30 days."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    as_of_dt = _parse_iso(result["as_of"])
    next_full = _parse_iso(result["moon_phase"]["next_full_moon"])
    next_new = _parse_iso(result["moon_phase"]["next_new_moon"])

    assert next_full > as_of_dt
    assert next_new > as_of_dt
    # The synodic month is ~29.53 days; allow a small slack.
    assert (next_full - as_of_dt).total_seconds() <= 30 * 24 * 3600
    assert (next_new - as_of_dt).total_seconds() <= 30 * 24 * 3600


# ── Next sign change / next event ────────────────────────────────────────────


def test_next_sign_change_is_consistent_and_in_the_future() -> None:
    """``next_sign_change`` names a graha, a from/to sign, and a future ``at``."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    nsc = result["next_sign_change"]
    assert nsc is not None
    assert nsc["planet"] in GRAHA_ORDER
    assert nsc["from"] in SIGNS
    assert nsc["to"] in SIGNS
    assert nsc["from"] != nsc["to"]
    at_dt = _parse_iso(nsc["at"])
    as_of_dt = _parse_iso(result["as_of"])
    assert at_dt > as_of_dt


def test_next_event_mirrors_next_sign_change_when_that_is_the_default() -> None:
    """When the next event is a sign change, ``next_event`` carries the same
    fields plus a ``type`` discriminator."""
    result = get_current_sky(as_of=FIXED_AS_OF)
    nsc = result["next_sign_change"]
    nxt = result["next_event"]
    assert nxt is not None
    assert nxt["type"] == "sign_change"
    for key in ("planet", "from", "to", "at"):
        assert nxt[key] == nsc[key]


# ── Error path: unparseable as_of ────────────────────────────────────────────


@pytest.mark.parametrize(
    "bad_as_of",
    [
        "not-a-date",                 # plain garbage
        "2024-13-01T00:00:00Z",       # impossible month
        "2024/06/15 12:00",           # wrong separator
        "yesterday",                  # natural-language
        "",                           # empty string
    ],
)
def test_unparseable_as_of_raises_value_error(bad_as_of: str) -> None:
    """Requirement 9.4: unparseable ``as_of`` raises ``ValueError``."""
    with pytest.raises(ValueError):
        get_current_sky(as_of=bad_as_of)


def test_non_string_as_of_raises_value_error() -> None:
    """A non-string ``as_of`` (e.g. int, list) is also a ``ValueError``."""
    with pytest.raises(ValueError):
        get_current_sky(as_of=12345)  # type: ignore[arg-type]


# ── Timezone handling ────────────────────────────────────────────────────────


def test_as_of_with_explicit_offset_is_normalized_to_utc() -> None:
    """``2024-06-15T17:30:00+05:30`` is the same instant as ``12:00:00Z``."""
    result_utc = get_current_sky(as_of="2024-06-15T12:00:00Z")
    result_ist = get_current_sky(as_of="2024-06-15T17:30:00+05:30")
    # Same instant ⇒ same planetary snapshot.
    assert result_utc["planets"] == result_ist["planets"]
    assert result_utc["moon_phase"]["name"] == result_ist["moon_phase"]["name"]
