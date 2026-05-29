"""Unit tests for the extended ``AgentState`` TypedDict."""

from __future__ import annotations

from app.agent.state import AgentState, BirthDetails


# Fields added in Phase 4 to support sensitivity HiTL and structured streaming.
NEW_FIELDS = {
    "sensitive_category": "health",
    "confirmation_preview": "This touches a sensitive area...",
    "confirmed": True,
    "chart_svg": "<svg></svg>",
    "structured_card": {"card_type": "transit", "data": {"planet": "Saturn"}},
}

# Pre-existing fields that must be preserved by the extension.
EXISTING_FIELDS = {
    "user_id": "user-123",
    "session_id": "sess-abc",
    "language": "en",
    "birth_details": BirthDetails(
        date="1995-05-12",
        time="04:30:00",
        place="Pune, India",
        lat=18.5204,
        lng=73.8567,
        timezone="Asia/Kolkata",
    ),
    "natal_chart": {"ascendant": "Aries", "planets": []},
    "active_dashas": {"maha": {"lord": "Venus"}},
    "intent": "chart_request",
    "tool_outputs": [{"tool": "compute_birth_chart", "result": {}}],
    "draft_response": "Your Lagna is Aries...",
    "sensitive_flag": False,
    "awaiting_confirmation": False,
    "messages": [],
}


def test_empty_state_is_valid_total_false() -> None:
    """``total=False`` means an empty dict is a valid ``AgentState``."""
    state: AgentState = {}
    assert state == {}
    # All declared fields must be optional.
    assert AgentState.__total__ is False


def test_state_with_only_new_fields() -> None:
    """A state containing only the new Phase 4 fields is valid and round-trips."""
    state: AgentState = {
        "sensitive_category": NEW_FIELDS["sensitive_category"],
        "confirmation_preview": NEW_FIELDS["confirmation_preview"],
        "confirmed": NEW_FIELDS["confirmed"],
        "chart_svg": NEW_FIELDS["chart_svg"],
        "structured_card": NEW_FIELDS["structured_card"],
    }
    for key, value in NEW_FIELDS.items():
        assert state[key] == value


def test_state_with_only_existing_fields() -> None:
    """Existing fields are still accepted on their own without the new fields."""
    state: AgentState = dict(EXISTING_FIELDS)
    for key, value in EXISTING_FIELDS.items():
        assert state[key] == value
    # None of the new fields are required.
    for key in NEW_FIELDS:
        assert key not in state


def test_state_with_all_fields_combined() -> None:
    """Existing and new fields coexist and are preserved verbatim."""
    state: AgentState = {**EXISTING_FIELDS, **NEW_FIELDS}
    for key, value in EXISTING_FIELDS.items():
        assert state[key] == value
    for key, value in NEW_FIELDS.items():
        assert state[key] == value


def test_each_new_field_can_be_omitted_individually() -> None:
    """Dropping any single new field still produces a valid state dict."""
    full: AgentState = {**EXISTING_FIELDS, **NEW_FIELDS}
    for omitted in NEW_FIELDS:
        partial: AgentState = {k: v for k, v in full.items() if k != omitted}
        assert omitted not in partial
        # Sibling new fields remain intact.
        for sibling in NEW_FIELDS:
            if sibling == omitted:
                continue
            assert partial[sibling] == NEW_FIELDS[sibling]


def test_optional_payloads_accept_none() -> None:
    """``chart_svg`` and ``structured_card`` are typed ``| None`` and accept None."""
    state: AgentState = {"chart_svg": None, "structured_card": None}
    assert state["chart_svg"] is None
    assert state["structured_card"] is None


def test_new_fields_declared_on_typed_dict() -> None:
    """All new field names appear in the TypedDict's annotations."""
    annotations = AgentState.__annotations__
    for key in NEW_FIELDS:
        assert key in annotations, f"missing field: {key}"


def test_existing_fields_still_declared() -> None:
    """The extension preserves every previously declared field name."""
    annotations = AgentState.__annotations__
    expected_existing = {
        "messages",
        "user_id",
        "session_id",
        "language",
        "birth_details",
        "natal_chart",
        "active_dashas",
        "intent",
        "tool_outputs",
        "draft_response",
        "sensitive_flag",
        "awaiting_confirmation",
    }
    missing = expected_existing - set(annotations)
    assert not missing, f"existing fields lost: {sorted(missing)}"


def test_birth_details_is_total_false_too() -> None:
    """``BirthDetails`` keeps ``total=False`` so partial profiles remain valid."""
    assert BirthDetails.__total__ is False
    partial: BirthDetails = {"date": "1995-05-12"}
    assert partial == {"date": "1995-05-12"}
