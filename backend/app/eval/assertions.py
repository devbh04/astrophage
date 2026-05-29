"""
Deterministic assertions for the offline evaluation harness.

Each assertion is a pure function over `(case, run_record)` returning
``{"name": str, "passed": bool, "detail": str}``.
"""

from __future__ import annotations

from typing import Iterable


def _assertion(name: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def assert_tool_sequence_contains(case: dict, run_record: dict) -> dict:
    expected: list[str] = list((case.get("expected_tools") or []))
    actual: list[str] = list(run_record.get("tool_sequence") or [])
    if not expected:
        return _assertion("tool_sequence_contains", True, "no expected tools")
    missing = [t for t in expected if t not in actual]
    return _assertion(
        "tool_sequence_contains",
        not missing,
        f"missing={missing} actual={actual}" if missing else f"actual={actual}",
    )


def assert_chart_math(case: dict, run_record: dict) -> dict:
    """If the run produced a natal chart, assert ascendant + 9 grahas."""
    chart = (run_record.get("artifacts") or {}).get("natal_chart") or run_record.get("natal_chart")
    if not chart:
        return _assertion("chart_math", True, "no chart in run record")

    asc_sign = (chart.get("ascendant") or {}).get("sign")
    expected_asc = (case.get("assertions") or {}).get("chart_ascendant_sign")
    asc_ok = expected_asc is None or asc_sign == expected_asc
    planet_names = {p.get("name") for p in (chart.get("planets") or [])}
    expected_grahas = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    grahas_ok = expected_grahas.issubset(planet_names)
    expected_count = (case.get("assertions") or {}).get("chart_planets_count", 9)
    count_ok = len(planet_names) >= expected_count
    passed = asc_ok and grahas_ok and count_ok
    return _assertion(
        "chart_math",
        passed,
        f"asc={asc_sign} planets={sorted(planet_names)} expected_count={expected_count}",
    )


def assert_dasha_dates(case: dict, run_record: dict) -> dict:
    dashas = (run_record.get("artifacts") or {}).get("dashas") or run_record.get("active_dashas")
    if not dashas:
        return _assertion("dasha_dates", True, "no dasha record")
    timeline = dashas.get("timeline") or []
    total_years = sum(seg.get("years", 0) for seg in timeline)
    span_ok = total_years >= 120
    active = dashas.get("active") or {}
    has_active = bool(active.get("maha"))
    return _assertion(
        "dasha_dates",
        span_ok and has_active,
        f"timeline_years={total_years} has_active={has_active}",
    )


def assert_guardrails(case: dict, run_record: dict) -> dict:
    """No `must_not_contain` token may appear in `final_response`."""
    must_not = (case.get("assertions") or {}).get("must_not_contain") or []
    response = (run_record.get("final_response") or "").lower()
    hits = [tok for tok in must_not if tok and tok.lower() in response]
    return _assertion(
        "guardrails",
        not hits,
        f"hits={hits}" if hits else "ok",
    )


def assert_language_match(case: dict, run_record: dict) -> dict:
    expected = case.get("expected_language")
    actual = run_record.get("detected_language")
    if not expected:
        return _assertion("language_match", True, "no expected_language")
    return _assertion(
        "language_match",
        expected == actual,
        f"expected={expected} detected={actual}",
    )


def assert_step_budget(case: dict, run_record: dict) -> dict:
    budget = (case.get("assertions") or {}).get("step_budget")
    if budget is None:
        return _assertion("step_budget", True, "no budget set")
    visits = run_record.get("node_visits", 0)
    return _assertion(
        "step_budget",
        visits <= budget,
        f"visits={visits} budget={budget}",
    )


ALL_ASSERTIONS = [
    assert_tool_sequence_contains,
    assert_chart_math,
    assert_dasha_dates,
    assert_guardrails,
    assert_language_match,
    assert_step_budget,
]


def run_assertions(case: dict, run_record: dict) -> list[dict]:
    return [fn(case, run_record) for fn in ALL_ASSERTIONS]


__all__ = [
    "assert_tool_sequence_contains",
    "assert_chart_math",
    "assert_dasha_dates",
    "assert_guardrails",
    "assert_language_match",
    "assert_step_budget",
    "run_assertions",
    "ALL_ASSERTIONS",
]
