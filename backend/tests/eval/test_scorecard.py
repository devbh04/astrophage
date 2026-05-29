"""Unit tests for ``app.eval.scorecard``.

Exercises the four invariants called out by Task 23:

1. One CSV row per case is appended to the scorecard.
2. Columns appear in the documented order.
3. The markdown summary aggregates correctly when grouped by category.
4. ``GOOGLE_API_KEY`` / ``QDRANT_API_KEY`` shaped substrings in ``comments``
   are redacted before persistence.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from app.eval.scorecard import (
    CSV_COLUMNS,
    ScorecardRow,
    append_row,
    append_rows,
    build_markdown_summary,
    print_markdown_summary,
    redact_secrets,
    row_from_record,
)


# ---------------------------------------------------------------------------
# Column-order invariant
# ---------------------------------------------------------------------------


def test_csv_columns_match_design_5_5_documented_order() -> None:
    """Per design §5.5 / Requirement 15.5, the column order is fixed."""
    assert CSV_COLUMNS == (
        "run_id",
        "timestamp",
        "case_id",
        "category",
        "language",
        "passed",
        "deterministic_score",
        "judge_avg",
        "comments",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(
    *,
    case_id: str = "ev_001",
    category: str = "valid_chart",
    language: str = "en",
    passed: bool = True,
    deterministic_score: float = 1.0,
    judge_avg: float | None = 4.5,
    comments: str = "ok",
) -> ScorecardRow:
    return ScorecardRow(
        run_id="run-2025-01-01",
        timestamp="2025-01-01T00:00:00Z",
        case_id=case_id,
        category=category,
        language=language,
        passed=passed,
        deterministic_score=deterministic_score,
        judge_avg=judge_avg,
        comments=comments,
    )


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    return header, rows


# ---------------------------------------------------------------------------
# CSV append: one row per case, header on first write, exact column order
# ---------------------------------------------------------------------------


def test_append_row_creates_file_with_header_in_documented_order(tmp_path: Path) -> None:
    target = tmp_path / "scorecard.csv"
    row = _make_row()

    written = append_row(row, path=target)

    assert written == target
    assert target.exists()

    with target.open(encoding="utf-8") as handle:
        first_line = handle.readline().rstrip("\r\n")

    # The header line is the documented column list, comma-joined.
    assert first_line == ",".join(CSV_COLUMNS)


def test_append_row_writes_one_row_per_case(tmp_path: Path) -> None:
    target = tmp_path / "scorecard.csv"

    cases = [
        _make_row(case_id="ev_001", category="valid_chart"),
        _make_row(case_id="ev_002", category="vedic_query"),
        _make_row(case_id="ev_003", category="adversarial", passed=False, judge_avg=None),
    ]
    for row in cases:
        append_row(row, path=target)

    header, persisted = _read_rows(target)

    assert header == list(CSV_COLUMNS)
    assert len(persisted) == len(cases)
    assert [r["case_id"] for r in persisted] == ["ev_001", "ev_002", "ev_003"]
    # ``judge_avg`` is empty (not the literal string ``None``) when omitted.
    assert persisted[2]["judge_avg"] == ""
    # ``passed`` round-trips as the python ``bool`` repr through csv.
    assert persisted[0]["passed"] == "True"
    assert persisted[2]["passed"] == "False"


def test_append_rows_batch_preserves_insertion_order(tmp_path: Path) -> None:
    target = tmp_path / "scorecard.csv"

    rows = [_make_row(case_id=f"ev_{i:03d}") for i in range(5)]
    append_rows(rows, path=target)

    header, persisted = _read_rows(target)
    assert header == list(CSV_COLUMNS)
    assert [r["case_id"] for r in persisted] == [f"ev_{i:03d}" for i in range(5)]


def test_append_row_appends_to_existing_file_without_duplicating_header(
    tmp_path: Path,
) -> None:
    target = tmp_path / "scorecard.csv"

    append_row(_make_row(case_id="ev_001"), path=target)
    append_row(_make_row(case_id="ev_002"), path=target)
    append_row(_make_row(case_id="ev_003"), path=target)

    with target.open(encoding="utf-8") as handle:
        lines = [line.rstrip("\r\n") for line in handle if line.strip()]

    # 1 header + 3 data lines.
    assert len(lines) == 4
    assert lines[0] == ",".join(CSV_COLUMNS)
    # Header appears exactly once.
    assert sum(1 for line in lines if line == ",".join(CSV_COLUMNS)) == 1


def test_append_creates_missing_parent_directory(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deeper" / "scorecard.csv"
    append_row(_make_row(), path=target)
    assert target.exists()


# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,must_contain_redacted,must_not_contain",
    [
        # AIza-shaped Google key.
        (
            "Embedding failed: AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy",
            "<redacted>",
            "AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy",
        ),
        # GOOGLE_API_KEY assignment with quotes.
        (
            'env GOOGLE_API_KEY="AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy"',
            "<redacted>",
            "AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy",
        ),
        # QDRANT_API_KEY in JSON-ish dict.
        (
            'config: {"QDRANT_API_KEY": "abcdef.GHIJKLMNOPQRS.tuvwxyz0123456789AB"}',
            "<redacted>",
            "abcdef.GHIJKLMNOPQRS.tuvwxyz0123456789AB",
        ),
        # Plain colon-separated form.
        (
            "GOOGLE_API_KEY: super-secret-value-1234",
            "<redacted>",
            "super-secret-value-1234",
        ),
        # Lowercase env-var name (case insensitive match).
        (
            "google_api_key=mySecretValue",
            "<redacted>",
            "mySecretValue",
        ),
        # Bare JWT-shaped Qdrant token (three base64url segments).
        (
            "auth header eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c there",
            "<redacted>",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ),
    ],
)
def test_redact_secrets_replaces_key_shaped_substrings(
    raw: str, must_contain_redacted: str, must_not_contain: str
) -> None:
    redacted = redact_secrets(raw)
    assert must_contain_redacted in redacted
    assert must_not_contain not in redacted


def test_redact_secrets_preserves_innocent_text() -> None:
    safe = "Case ev_010 passed all assertions; tool sequence had 3 calls."
    assert redact_secrets(safe) == safe


def test_redact_secrets_handles_none_and_empty() -> None:
    assert redact_secrets(None) == ""
    assert redact_secrets("") == ""


def test_redact_secrets_keeps_key_name_for_debuggability() -> None:
    raw = 'GOOGLE_API_KEY="AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy"'
    redacted = redact_secrets(raw)
    # We keep the variable name in the message so an operator can still tell
    # which secret leaked, but the value itself is gone.
    assert "GOOGLE_API_KEY" in redacted
    assert "<redacted>" in redacted
    assert "AIza" not in redacted


def test_appended_comments_are_redacted_in_csv(tmp_path: Path) -> None:
    target = tmp_path / "scorecard.csv"
    leaked = (
        "tool error: GOOGLE_API_KEY=AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy "
        "and QDRANT_API_KEY=abcdef.GHIJKLMNOPQRS.tuvwxyz0123456789AB"
    )
    append_row(_make_row(comments=leaked), path=target)

    raw = target.read_text(encoding="utf-8")
    assert "AIzaSyA1234567890abcdefghijKLMNOPqrstuvwxy" not in raw
    assert "abcdef.GHIJKLMNOPQRS.tuvwxyz0123456789AB" not in raw
    assert "<redacted>" in raw
    # Variable names are preserved for operator triage.
    assert "GOOGLE_API_KEY" in raw
    assert "QDRANT_API_KEY" in raw


# ---------------------------------------------------------------------------
# Markdown summary aggregation
# ---------------------------------------------------------------------------


def test_markdown_summary_groups_by_category_and_aggregates_correctly() -> None:
    rows = [
        _make_row(case_id="a1", category="valid_chart", passed=True,
                  deterministic_score=1.0, judge_avg=4.0),
        _make_row(case_id="a2", category="valid_chart", passed=False,
                  deterministic_score=0.5, judge_avg=2.0),
        _make_row(case_id="b1", category="vedic_query", passed=True,
                  deterministic_score=1.0, judge_avg=5.0),
        _make_row(case_id="c1", category="adversarial", passed=False,
                  deterministic_score=0.0, judge_avg=None),
    ]

    summary = build_markdown_summary(rows)
    lines = summary.splitlines()

    # Header + separator + 3 category rows + 1 ALL row = 6 lines.
    assert len(lines) == 6
    assert lines[0].startswith(
        "| Category | Cases | Passed | Pass Rate | Det. Score | Judge Avg |"
    )
    assert lines[1].startswith("| --- |")

    # Categories are sorted alphabetically: adversarial, valid_chart, vedic_query.
    assert lines[2].startswith("| adversarial |")
    assert lines[3].startswith("| valid_chart |")
    assert lines[4].startswith("| vedic_query |")
    assert lines[5].startswith("| **ALL** |")

    # adversarial: 1 case, 0 passed, pass_rate 0.00, det 0.00, judge n/a.
    assert "| adversarial | 1 | 0 | 0.00 | 0.00 | n/a |" in lines[2]
    # valid_chart: 2 cases, 1 passed, pass_rate 0.50, det 0.75, judge 3.00.
    assert "| valid_chart | 2 | 1 | 0.50 | 0.75 | 3.00 |" in lines[3]
    # vedic_query: 1 case, 1 passed, pass_rate 1.00, det 1.00, judge 5.00.
    assert "| vedic_query | 1 | 1 | 1.00 | 1.00 | 5.00 |" in lines[4]
    # ALL: 4 cases, 2 passed, pass_rate 0.50, det avg = (1+0.5+1+0)/4 = 0.625
    # -> "0.62" (banker's rounding) or "0.63" depending on format spec; the
    # default ``f"{0.625:.2f}"`` is "0.62".
    assert "| **ALL** | 4 | 2 | 0.50 | 0.62 |" in lines[5]
    # judge avg over the 3 non-None values: (4+2+5)/3 = 3.6666... -> "3.67".
    assert lines[5].endswith("| 3.67 |")


def test_markdown_summary_handles_empty_rows() -> None:
    summary = build_markdown_summary([])
    assert "_no rows_" in summary
    assert "| Category |" in summary


def test_markdown_summary_judge_avg_na_when_all_judges_missing() -> None:
    rows = [
        _make_row(case_id="x", category="multilingual", judge_avg=None),
        _make_row(case_id="y", category="multilingual", judge_avg=None),
    ]
    summary = build_markdown_summary(rows)
    # Both the category row and ALL row should report n/a for judge avg.
    for line in summary.splitlines()[2:]:
        assert line.endswith("| n/a |")


def test_print_markdown_summary_writes_to_stream() -> None:
    rows = [_make_row(case_id="a", category="valid_chart")]
    buffer = io.StringIO()
    rendered = print_markdown_summary(rows, stream=buffer)
    written = buffer.getvalue()
    assert rendered in written
    assert written.endswith("\n")


# ---------------------------------------------------------------------------
# row_from_record convenience
# ---------------------------------------------------------------------------


def test_row_from_record_accepts_loose_mapping() -> None:
    record = {
        "run_id": "r1",
        "timestamp": "2025-01-01T00:00:00Z",
        "case_id": "ev_007",
        "category": "graceful_failure",
        "language": "hi",
        "passed": False,
        "deterministic_score": 0.5,
        "judge_avg": 3.25,
        "comments": "missing birth time",
    }
    row = row_from_record(record)
    assert row.case_id == "ev_007"
    assert row.judge_avg == pytest.approx(3.25)
    assert row.comments == "missing birth time"


def test_row_from_record_treats_empty_judge_avg_as_none() -> None:
    record = {"case_id": "ev_001", "judge_avg": ""}
    row = row_from_record(record)
    assert row.judge_avg is None
