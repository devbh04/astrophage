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
    "latency_ms",
    "tool_calls",
    "input_tokens",
    "output_tokens",
    "est_cost_usd",
    "failure",
    "comments",
]


# Estimated USD price per 1k tokens for the default chat model. These are
# approximate and meant to give the eval scorecard a realistic order of
# magnitude; update them whenever the underlying model pricing changes.
# Source: Vertex AI Gemini 2.5 Flash list price as of May 2026.
DEFAULT_INPUT_PRICE_PER_1K = 0.000075   # $/1k input tokens
DEFAULT_OUTPUT_PRICE_PER_1K = 0.0003    # $/1k output tokens


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    """Approximate USD cost for one turn given token counts."""
    return (
        (input_tokens or 0) * DEFAULT_INPUT_PRICE_PER_1K / 1000.0
        + (output_tokens or 0) * DEFAULT_OUTPUT_PRICE_PER_1K / 1000.0
    )


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


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * pct
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def markdown_summary(rows: list[dict]) -> str:
    """Produce a markdown summary grouped by category + a run-level aggregate."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_cat[row.get("category", "uncategorized")].append(row)

    lines = ["# Eval scorecard", ""]
    lines.append(
        "| Category | Cases | Passed | Deterministic | Judge avg | "
        "Avg tools | p50 ms | p95 ms | Cost $ |"
    )
    lines.append(
        "|----------|-------|--------|---------------|-----------|"
        "-----------|--------|--------|--------|"
    )
    overall_passed = 0
    overall_total = 0
    overall_failures = 0
    overall_latencies: list[float] = []
    overall_tools: list[float] = []
    overall_cost = 0.0
    overall_input_tokens = 0
    overall_output_tokens = 0
    for cat in sorted(by_cat):
        rows_ = by_cat[cat]
        cases = len(rows_)
        passed = sum(1 for r in rows_ if str(r.get("passed")).lower() == "true")
        det_avg = (
            sum(float(r.get("deterministic_score") or 0) for r in rows_) / cases
            if cases else 0.0
        )
        judges = [
            float(r.get("judge_avg") or 0)
            for r in rows_
            if r.get("judge_avg") not in (None, "", "null")
        ]
        judge_avg = sum(judges) / len(judges) if judges else 0.0
        tool_counts = [int(r.get("tool_calls") or 0) for r in rows_]
        avg_tools = sum(tool_counts) / cases if cases else 0.0
        latencies = [float(r.get("latency_ms") or 0) for r in rows_]
        p50 = _percentile(latencies, 0.50)
        p95 = _percentile(latencies, 0.95)
        cat_cost = sum(float(r.get("est_cost_usd") or 0) for r in rows_)
        cat_failures = sum(
            1 for r in rows_ if str(r.get("failure")).lower() == "true"
        )
        lines.append(
            f"| {cat} | {cases} | {passed} | {det_avg:.2f} | {judge_avg:.2f} | "
            f"{avg_tools:.1f} | {p50:.0f} | {p95:.0f} | {cat_cost:.4f} |"
        )
        overall_passed += passed
        overall_total += cases
        overall_failures += cat_failures
        overall_latencies.extend(latencies)
        overall_tools.extend(tool_counts)
        overall_cost += cat_cost
        overall_input_tokens += sum(int(r.get("input_tokens") or 0) for r in rows_)
        overall_output_tokens += sum(int(r.get("output_tokens") or 0) for r in rows_)

    lines.append("")
    lines.append("## Run-level totals")
    lines.append("")
    lines.append(f"- Cases: **{overall_total}**")
    lines.append(
        f"- Passed: **{overall_passed}** "
        f"({(overall_passed / overall_total * 100) if overall_total else 0:.1f}%)"
    )
    lines.append(
        f"- Failures (raised exceptions): **{overall_failures}** "
        f"({(overall_failures / overall_total * 100) if overall_total else 0:.1f}%)"
    )
    lines.append(
        f"- Avg tool calls / case: **"
        f"{(sum(overall_tools) / overall_total) if overall_total else 0:.1f}**"
    )
    lines.append(f"- Latency p50: **{_percentile(overall_latencies, 0.50):.0f} ms**")
    lines.append(f"- Latency p95: **{_percentile(overall_latencies, 0.95):.0f} ms**")
    lines.append(f"- Total input tokens: **{overall_input_tokens}**")
    lines.append(f"- Total output tokens: **{overall_output_tokens}**")
    lines.append(f"- Estimated cost: **${overall_cost:.4f}**")
    return "\n".join(lines)


def append_run_log(
    path: Path,
    *,
    run_id: str,
    timestamp: str,
    rows: list[dict],
) -> None:
    """
    Append a single one-line summary of this run to a markdown log so
    drift across runs is visible at a glance. Creates the file with a
    header on first write.
    """
    if not rows:
        return
    total = len(rows)
    passed = sum(1 for r in rows if str(r.get("passed")).lower() == "true")
    failures = sum(1 for r in rows if str(r.get("failure")).lower() == "true")
    judges = [
        float(r.get("judge_avg") or 0)
        for r in rows
        if r.get("judge_avg") not in (None, "", "null")
    ]
    judge_avg = sum(judges) / len(judges) if judges else 0.0
    det_avg = (
        sum(float(r.get("deterministic_score") or 0) for r in rows) / total
    )
    latencies = [float(r.get("latency_ms") or 0) for r in rows]
    p50 = _percentile(latencies, 0.50)
    p95 = _percentile(latencies, 0.95)
    cost = sum(float(r.get("est_cost_usd") or 0) for r in rows)
    avg_tools = sum(int(r.get("tool_calls") or 0) for r in rows) / total

    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8") as fh:
        if is_new:
            fh.write(
                "# AstroAgent eval run history\n\n"
                "Each row is one invocation of `python -m app.eval.run`. "
                "Compare adjacent rows to spot regressions.\n\n"
                "| run_id | timestamp | cases | passed | failures | "
                "det_avg | judge_avg | avg_tools | p50 ms | p95 ms | cost $ |\n"
                "|--------|-----------|-------|--------|----------|"
                "---------|-----------|-----------|--------|--------|--------|\n"
            )
        fh.write(
            f"| `{run_id}` | {timestamp} | {total} | {passed} | {failures} | "
            f"{det_avg:.2f} | {judge_avg:.2f} | {avg_tools:.1f} | "
            f"{p50:.0f} | {p95:.0f} | {cost:.4f} |\n"
        )


def now_run_id() -> str:
    return datetime.now(tz=timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")


def now_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


__all__ = [
    "CSV_COLUMNS",
    "DEFAULT_INPUT_PRICE_PER_1K",
    "DEFAULT_OUTPUT_PRICE_PER_1K",
    "estimate_cost_usd",
    "append_row",
    "append_run_log",
    "write_scorecard",
    "markdown_summary",
    "redact_comments",
    "now_run_id",
    "now_timestamp",
]
