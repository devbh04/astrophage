"""Unit tests for backend/eval/golden_set.jsonl.

Validates the golden evaluation set has exactly 30 well-formed JSON lines,
required fields are present on every case, the per-category distribution
matches design §5.1, and `expected_language` is one of the supported codes.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

REPO_BACKEND = Path(__file__).resolve().parents[2]
GOLDEN_PATH = REPO_BACKEND / "eval" / "golden_set.jsonl"

REQUIRED_TOP_LEVEL_FIELDS = {
    "id",
    "category",
    "input",
    "natal_chart",
    "expected_language",
    "expected_tools",
    "assertions",
    "judge_rubric",
}

REQUIRED_ASSERTIONS_KEYS = {"must_not_contain", "step_budget"}

VALID_CATEGORIES = {
    "valid_chart",
    "vedic_query",
    "multilingual",
    "graceful_failure",
    "adversarial",
}

EXPECTED_CATEGORY_COUNTS = {
    "valid_chart": 10,
    "vedic_query": 8,
    "multilingual": 5,
    "graceful_failure": 4,
    "adversarial": 3,
}

VALID_LANGUAGES = {"en", "hi", "mr", "gu", "ta", "kn"}


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    assert GOLDEN_PATH.exists(), f"golden set missing at {GOLDEN_PATH}"
    raw_lines = GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    # Drop trailing blank line if present, but blank lines between cases are
    # not allowed.
    parsed: list[dict] = []
    for idx, line in enumerate(raw_lines, start=1):
        if not line.strip():
            pytest.fail(f"line {idx} is blank; golden set must have no blank lines")
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError as exc:
            pytest.fail(f"line {idx} is not valid JSON: {exc}")
    return parsed


def test_golden_set_has_exactly_30_lines(cases: list[dict]) -> None:
    assert len(cases) == 30, f"expected 30 cases, found {len(cases)}"


def test_every_line_has_required_fields(cases: list[dict]) -> None:
    for case in cases:
        missing = REQUIRED_TOP_LEVEL_FIELDS - set(case.keys())
        assert not missing, f"case {case.get('id')!r} missing fields {missing}"
        assert isinstance(case["id"], str) and case["id"], "id must be non-empty str"
        assert isinstance(case["category"], str)
        assert isinstance(case["input"], str) and case["input"]
        assert case["natal_chart"] is None or isinstance(case["natal_chart"], dict)
        assert isinstance(case["expected_language"], str)
        assert isinstance(case["expected_tools"], list)
        assert all(isinstance(t, str) for t in case["expected_tools"])
        assert isinstance(case["assertions"], dict)
        assert isinstance(case["judge_rubric"], list) and case["judge_rubric"]


def test_assertions_block_has_minimum_keys(cases: list[dict]) -> None:
    for case in cases:
        missing = REQUIRED_ASSERTIONS_KEYS - set(case["assertions"].keys())
        assert not missing, (
            f"case {case['id']!r} assertions missing keys {missing}"
        )
        assert isinstance(case["assertions"]["must_not_contain"], list)
        assert isinstance(case["assertions"]["step_budget"], int)
        assert case["assertions"]["step_budget"] > 0


def test_ids_are_unique(cases: list[dict]) -> None:
    ids = [c["id"] for c in cases]
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    assert not duplicates, f"duplicate case ids: {duplicates}"


def test_categories_are_valid(cases: list[dict]) -> None:
    for case in cases:
        assert case["category"] in VALID_CATEGORIES, (
            f"case {case['id']!r} has unknown category {case['category']!r}"
        )


def test_category_distribution_matches_design(cases: list[dict]) -> None:
    counts = Counter(c["category"] for c in cases)
    assert dict(counts) == EXPECTED_CATEGORY_COUNTS, (
        f"category distribution mismatch: got {dict(counts)}, "
        f"expected {EXPECTED_CATEGORY_COUNTS}"
    )


def test_expected_language_is_supported(cases: list[dict]) -> None:
    for case in cases:
        assert case["expected_language"] in VALID_LANGUAGES, (
            f"case {case['id']!r} expected_language "
            f"{case['expected_language']!r} not in {VALID_LANGUAGES}"
        )


def test_multilingual_distribution_covers_six_languages(cases: list[dict]) -> None:
    """The 10 valid_chart + 5 multilingual cases together should exercise all
    six supported languages so the harness covers each script."""
    chart_and_multilingual = [
        c for c in cases if c["category"] in {"valid_chart", "multilingual"}
    ]
    languages = {c["expected_language"] for c in chart_and_multilingual}
    assert languages == VALID_LANGUAGES, (
        f"chart + multilingual cases cover {languages}, "
        f"expected all of {VALID_LANGUAGES}"
    )
