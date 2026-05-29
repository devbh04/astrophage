"""
Evaluation scorecard — append CSV rows + print markdown summary.
"""

from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


CSV_COLUMNS = [
    "run_id",
    "timestamp",
    "case_id",
    "category",
    "language",
    "passed",
    "deterministic_score",
    "judge_avg",
    "comments",
]


# Anything that looks like an API key value should be redacted.
SECRET_RE = re.compile(
    r"(?:GOOGLE_API_KEY|QDRANT_API_KEY|JWT_SECRET)\s*[=:]\s*[\w\-]+"
)
# bare key-shaped strings ≥ 24 chars
BARE_KEY_RE = re.compile(r"\bAIza[\w-]{20,}\b")


def redact_comments(text: str) -> str:
    if not text:
        return ""
    out = SECRET_RE.sub("[redacted]", text)
    out = BARE_KEY_RE.sub("[redacted]", out)
    return out


def _ensure_header(path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)


def append_row(
    path: Path,
    row: dict,
) -> None:
    """Append a single scorecard row. Creates the file with a header if needed."""
    _ensure_header(path)
    safe_row = dict(row)
    safe_row["comments"] = redact_comments(str(safe_row.get("comments", "")))
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([safe_row.get(col, "") for col in CSV_COLUMNS])


def write_scorecard(
    path: Path,
    rows: Iterable[dict],
) -> None:
    """Append many rows in order."""
    _ensure_header(path)
    for row in rows:
        append_row(path, row)


def markdown_summary(rows: list[dict]) -> str:
    """Produce a markdown summary grouped by category."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_cat[row.get("category", "uncategorized")].append(row)

    lines = ["# Eval scorecard", ""]
    lines.append("| Category | Cases | Passed | Deterministic | Judge avg |")
    lines.append("|----------|-------|--------|---------------|-----------|")
    overall_passed = 0
    overall_total = 0
    for cat in sorted(by_cat):
        rows_ = by_cat[cat]
        cases = len(rows_)
        passed = sum(1 for r in rows_ if str(r.get("passed")).lower() == "true")
        det_avg = (
            sum(float(r.get("deterministic_score") or 0) for r in rows_) / cases
            if cases else 0.0
        )
        judges = [float(r.get("judge_avg") or 0) for r in rows_ if r.get("judge_avg") not in (None, "", "null")]
        judge_avg = sum(judges) / len(judges) if judges else 0.0
        lines.append(
            f"| {cat} | {cases} | {passed} | {det_avg:.2f} | {judge_avg:.2f} |"
        )
        overall_passed += passed
        overall_total += cases
    lines.append("")
    lines.append(f"**Overall pass rate: {overall_passed}/{overall_total}**")
    return "\n".join(lines)


def now_run_id() -> str:
    return datetime.now(tz=timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def now_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


__all__ = [
    "CSV_COLUMNS",
    "append_row",
    "write_scorecard",
    "markdown_summary",
    "redact_comments",
    "now_run_id",
    "now_timestamp",
]
