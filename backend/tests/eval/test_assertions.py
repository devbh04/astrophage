"""Unit tests for ``app.eval.assertions``.

Each public assertion has explicit pass and fail paths exercised with
realistic synthetic ``(case, run_record)`` tuples. The fixtures below model
what the eval runner will actually populate (per design §5.2/§5.3) so the
tests stay representative without dragging in live dependencies.
"""

from __future__ import annotations

import pytest

from app.eval.assertions import (
    CANONICAL_GRAHAS,
    assert_chart_math,
    assert_dasha_dates,
    assert_guardrails,
    assert_language_match,
    assert_step_budget,
    assert_tool_sequence_contains,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


def _case(**overrides) -> dict:
    """Realistic golden-set case (English chart request)."""
    base = {
        "id": "ev_001",
        "category": "valid_chart",
        "input": "Generate my chart. Born 12 May 1995, 4:30 AM, Pune India.",
        "natal_chart": None,
        "expected_language": "en",
        "expected_tools": ["geocode_place", "compute_birth_chart"],
        "assertions": {
            "chart_planets_count": 9,
            "chart_ascendant_sign": "Aries",
            "must_contain": ["Lagna", "Aries"],
            "must_not_contain": ["fatal", "guaranteed"],
            "step_budget": 6,
        },
        "judge_rubric": ["warmth", "cultural_appropriateness", "helpfulness", "fluency"],
    }
    base.update(overrides)
    return base


def _natal_chart() -> dict:
    """Synthetic natal chart with all 9 grahas and ``Aries`` ascendant."""
    return {
        "ascendant": {"sign": "Aries", "degree": 12.34},
        "planets": [
            {"name": graha, "sign": "Taurus", "house": 2}
            for graha in CANONICAL_GRAHAS
        ],
    }


def _dashas() -> dict:
    """Synthetic Vimshottari record covering ~120 years with active block inside."""
    return {
        "balance_at_birth": {"lord": "Venus", "remaining_years": 18.0},
        "timeline": [
            {
                "lord": "Venus",
                "level": "maha",
                "start": "1995-05-12T00:00:00+00:00",
                "end": "2013-05-12T00:00:00+00:00",
                "years": 18.0,
            },
            {
                "lord": "Sun",
                "level": "maha",
                "start": "2013-05-12T00:00:00+00:00",
                "end": "2019-05-12T00:00:00+00:00",
                "years": 6.0,
            },
            {
                "lord": "Moon",
                "level": "maha",
                "start": "2019-05-12T00:00:00+00:00",
                "end": "2120-01-01T00:00:00+00:00",
                "years": 100.0,
            },
        ],
        "active": {
            "maha": {
                "lord": "Sun",
                "start": "2013-05-12T00:00:00+00:00",
                "end": "2019-05-12T00:00:00+00:00",
            },
            "antar": {
                "lord": "Mercury",
                "start": "2014-05-12T00:00:00+00:00",
                "end": "2014-11-12T00:00:00+00:00",
            },
        },
    }


def _run_record(**overrides) -> dict:
    """Realistic per-case run record produced by the eval runner."""
    base = {
        "tool_sequence": [
            "geocode_place",
            "compute_birth_chart",
            "compute_dasha_periods",
        ],
        "natal_chart": _natal_chart(),
        "active_dashas": _dashas(),
        "final_response": (
            "Your Lagna is Aries and the planetary placements look balanced "
            "across the chart. Let us walk through the highlights together."
        ),
        "detected_language": "en",
        "step_count": 5,
    }
    base.update(overrides)
    return base


# ── 1. assert_tool_sequence_contains ──────────────────────────────────────


def test_tool_sequence_pass_when_expected_subset_present() -> None:
    result = assert_tool_sequence_contains(_case(), _run_record())
    assert result["name"] == "tool_sequence_contains"
    assert result["passed"] is True


def test_tool_sequence_pass_with_no_expected_tools() -> None:
    result = assert_tool_sequence_contains(_case(expected_tools=[]), _run_record())
    assert result["passed"] is True
    assert "trivially satisfied" in result["detail"]


def test_tool_sequence_fail_when_expected_tool_missing() -> None:
    result = assert_tool_sequence_contains(
        _case(expected_tools=["geocode_place", "knowledge_lookup"]),
        _run_record(),
    )
    assert result["passed"] is False
    assert "knowledge_lookup" in result["detail"]


def test_tool_sequence_fail_when_observed_is_string() -> None:
    result = assert_tool_sequence_contains(
        _case(),
        _run_record(tool_sequence="geocode_place"),
    )
    assert result["passed"] is False


# ── 2. assert_chart_math ──────────────────────────────────────────────────


def test_chart_math_pass_with_full_chart() -> None:
    result = assert_chart_math(_case(), _run_record())
    assert result["name"] == "chart_math"
    assert result["passed"] is True


def test_chart_math_pass_with_plain_string_ascendant() -> None:
    chart = _natal_chart()
    chart["ascendant"] = "Aries"
    result = assert_chart_math(_case(), _run_record(natal_chart=chart))
    assert result["passed"] is True


def test_chart_math_fail_when_planet_count_wrong() -> None:
    chart = _natal_chart()
    chart["planets"] = chart["planets"][:8]  # drop Ketu
    result = assert_chart_math(_case(), _run_record(natal_chart=chart))
    assert result["passed"] is False
    assert "planet count" in result["detail"]


def test_chart_math_fail_when_graha_missing() -> None:
    chart = _natal_chart()
    # Replace Saturn with a duplicate Sun → count stays 9 but graha set breaks.
    chart["planets"] = [
        {"name": "Sun" if p["name"] == "Saturn" else p["name"], "sign": p["sign"], "house": 1}
        for p in chart["planets"]
    ]
    result = assert_chart_math(_case(), _run_record(natal_chart=chart))
    assert result["passed"] is False
    assert "Saturn" in result["detail"]


def test_chart_math_fail_when_ascendant_mismatch() -> None:
    chart = _natal_chart()
    chart["ascendant"] = {"sign": "Taurus"}
    result = assert_chart_math(_case(), _run_record(natal_chart=chart))
    assert result["passed"] is False
    assert "Taurus" in result["detail"]


def test_chart_math_fail_when_chart_absent() -> None:
    result = assert_chart_math(_case(), _run_record(natal_chart=None))
    assert result["passed"] is False


# ── 3. assert_dasha_dates ─────────────────────────────────────────────────


def test_dasha_dates_pass_with_full_timeline_and_active() -> None:
    result = assert_dasha_dates(_case(), _run_record())
    assert result["name"] == "dasha_dates"
    assert result["passed"] is True


def test_dasha_dates_pass_when_active_omitted_but_timeline_long_enough() -> None:
    dashas = _dashas()
    dashas.pop("active")
    result = assert_dasha_dates(_case(), _run_record(active_dashas=dashas))
    assert result["passed"] is True


def test_dasha_dates_fail_when_timeline_under_120_years() -> None:
    dashas = _dashas()
    dashas["timeline"][-1] = {
        "lord": "Moon",
        "level": "maha",
        "start": "2019-05-12T00:00:00+00:00",
        "end": "2030-05-12T00:00:00+00:00",  # span < 120y
        "years": 11.0,
    }
    result = assert_dasha_dates(_case(), _run_record(active_dashas=dashas))
    assert result["passed"] is False
    assert "< required 120" in result["detail"]


def test_dasha_dates_fail_when_active_outside_timeline() -> None:
    dashas = _dashas()
    dashas["active"]["maha"] = {
        "lord": "Saturn",
        "start": "2200-01-01T00:00:00+00:00",
        "end": "2210-01-01T00:00:00+00:00",
    }
    result = assert_dasha_dates(_case(), _run_record(active_dashas=dashas))
    assert result["passed"] is False
    assert "outside timeline" in result["detail"]


def test_dasha_dates_fail_when_segment_dates_unparseable() -> None:
    dashas = _dashas()
    dashas["timeline"][0]["start"] = "not-a-date"
    result = assert_dasha_dates(_case(), _run_record(active_dashas=dashas))
    assert result["passed"] is False


def test_dasha_dates_fail_when_record_missing() -> None:
    result = assert_dasha_dates(_case(), _run_record(active_dashas=None))
    assert result["passed"] is False


# ── 4. assert_guardrails ──────────────────────────────────────────────────


def test_guardrails_pass_when_no_forbidden_tokens_present() -> None:
    result = assert_guardrails(_case(), _run_record())
    assert result["name"] == "guardrails"
    assert result["passed"] is True


def test_guardrails_pass_when_no_assertions_block() -> None:
    case = _case()
    case.pop("assertions")
    result = assert_guardrails(case, _run_record())
    assert result["passed"] is True


def test_guardrails_pass_when_must_not_contain_empty() -> None:
    case = _case()
    case["assertions"]["must_not_contain"] = []
    result = assert_guardrails(case, _run_record())
    assert result["passed"] is True


def test_guardrails_fail_on_forbidden_token_case_insensitive() -> None:
    response = (
        "This outcome is fatal and the result is GUARANTEED. "
        "There is nothing to discuss further."
    )
    result = assert_guardrails(_case(), _run_record(final_response=response))
    assert result["passed"] is False
    assert "fatal" in result["detail"]
    assert "guaranteed" in result["detail"]


def test_guardrails_fail_when_response_not_a_string() -> None:
    result = assert_guardrails(_case(), _run_record(final_response=None))
    assert result["passed"] is False


# ── 5. assert_language_match ──────────────────────────────────────────────


def test_language_match_pass_for_english_response() -> None:
    result = assert_language_match(_case(), _run_record())
    assert result["name"] == "language_match"
    assert result["passed"] is True


def test_language_match_pass_for_hindi_devanagari_response() -> None:
    case = _case(expected_language="hi")
    response = (
        "आपका लग्न मेष राशि में है और ग्रहों की स्थिति समग्र रूप से संतुलित दिखाई देती है। "
        "आइए हम इसे चरण दर चरण देखते हैं।"
    )
    record = _run_record(final_response=response, detected_language="hi")
    result = assert_language_match(case, record)
    assert result["passed"] is True


def test_language_match_fail_when_languages_disagree() -> None:
    case = _case(expected_language="hi")
    result = assert_language_match(case, _run_record())  # English response
    assert result["passed"] is False
    assert "expected='hi'" in result["detail"]


def test_language_match_fail_when_response_empty() -> None:
    result = assert_language_match(_case(), _run_record(final_response="   "))
    assert result["passed"] is False


def test_language_match_fail_when_agent_reported_mismatch() -> None:
    record = _run_record(detected_language="hi")
    result = assert_language_match(_case(), record)
    assert result["passed"] is False
    assert "agent reported" in result["detail"]


# ── 6. assert_step_budget ─────────────────────────────────────────────────


def test_step_budget_pass_under_budget_with_step_count() -> None:
    result = assert_step_budget(_case(), _run_record(step_count=5))
    assert result["name"] == "step_budget"
    assert result["passed"] is True


def test_step_budget_pass_under_budget_with_node_visits_list() -> None:
    record = _run_record()
    record.pop("step_count")
    record["node_visits"] = [
        "language_detector", "router", "reasoning", "tool_executor", "response"
    ]
    result = assert_step_budget(_case(), record)
    assert result["passed"] is True


def test_step_budget_pass_when_no_budget_declared() -> None:
    case = _case()
    case["assertions"].pop("step_budget")
    result = assert_step_budget(case, _run_record())
    assert result["passed"] is True


def test_step_budget_fail_when_visits_exceed_budget() -> None:
    case = _case()
    case["assertions"]["step_budget"] = 3
    result = assert_step_budget(case, _run_record(step_count=8))
    assert result["passed"] is False
    assert "8" in result["detail"] and "3" in result["detail"]


def test_step_budget_fail_when_record_missing_visit_data() -> None:
    record = _run_record()
    record.pop("step_count")
    result = assert_step_budget(_case(), record)
    assert result["passed"] is False


def test_step_budget_fail_when_budget_not_a_positive_int() -> None:
    case = _case()
    case["assertions"]["step_budget"] = -1
    result = assert_step_budget(case, _run_record())
    assert result["passed"] is False


# ── Cross-cutting input validation ────────────────────────────────────────


@pytest.mark.parametrize(
    "fn",
    [
        assert_tool_sequence_contains,
        assert_chart_math,
        assert_dasha_dates,
        assert_guardrails,
        assert_language_match,
        assert_step_budget,
    ],
)
def test_assertions_raise_typeerror_on_non_mapping_inputs(fn) -> None:
    """All assertions reject non-mapping inputs as a TypeError, not silently."""
    with pytest.raises(TypeError):
        fn("not a mapping", _run_record())
    with pytest.raises(TypeError):
        fn(_case(), "not a mapping")


@pytest.mark.parametrize(
    "fn",
    [
        assert_tool_sequence_contains,
        assert_chart_math,
        assert_dasha_dates,
        assert_guardrails,
        assert_language_match,
        assert_step_budget,
    ],
)
def test_assertion_results_have_required_shape(fn) -> None:
    """Every assertion returns the documented ``{name, passed, detail}`` shape."""
    result = fn(_case(), _run_record())
    assert set(result.keys()) == {"name", "passed", "detail"}
    assert isinstance(result["name"], str) and result["name"]
    assert isinstance(result["passed"], bool)
    assert isinstance(result["detail"], str)
