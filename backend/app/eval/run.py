"""
Offline evaluation runner.

Usage:
    uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl
    uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge

External services (Gemini, Qdrant, Supabase, Nominatim) MUST be mocked at run
time. The runner itself does not patch anything; tests should patch
`app.agent.graph.agent_graph` and any tool clients before invoking
`run_eval`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Iterable

from app.eval.assertions import run_assertions
from app.eval.scorecard import (
    append_row,
    markdown_summary,
    now_run_id,
    now_timestamp,
)


def _read_cases(path: Path) -> list[dict]:
    cases: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    return cases


def _initial_state(case: dict) -> dict:
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=case.get("input", ""))],
        "user_id": "eval-user",
        "session_id": case.get("id", "eval"),
        "language": case.get("expected_language") or "en",
        "natal_chart": case.get("natal_chart") or {},
        "active_dashas": {},
        "intent": "",
        "tool_outputs": [],
        "sensitive_flag": False,
    }


async def _run_case(case: dict, judge: bool, agent_graph: Any) -> dict:
    from langdetect import DetectorFactory, detect  # type: ignore
    DetectorFactory.seed = 0

    state = _initial_state(case)
    config = {"configurable": {"thread_id": f"eval:{case['id']}"}}

    tool_sequence: list[str] = []
    final_text = ""
    node_visits = 0

    try:
        async for event in agent_graph.astream_events(state, config=config, version="v2"):
            etype = event.get("event")
            name = event.get("name")
            data = event.get("data") or {}
            if etype == "on_tool_start":
                tool_sequence.append(name or "")
            if etype == "on_chain_start":
                node_visits += 1
            if etype == "on_chain_end" and name == "response":
                output = data.get("output") or {}
                if output.get("draft_response"):
                    final_text = output["draft_response"]
    except Exception as exc:
        final_text = f"[error] {exc}"

    detected_language = case.get("expected_language") or "en"
    if final_text:
        try:
            detected_language = detect(final_text)
        except Exception:
            pass

    run_record = {
        "case_id": case.get("id"),
        "tool_sequence": tool_sequence,
        "final_response": final_text,
        "detected_language": detected_language,
        "node_visits": node_visits,
    }
    assertions = run_assertions(case, run_record)
    deterministic_pass = sum(1 for a in assertions if a["passed"]) / max(1, len(assertions))
    record = {
        **run_record,
        "assertions": assertions,
        "deterministic_score": round(deterministic_pass, 4),
        "judge": None,
    }

    if judge:
        from app.eval.judge import judge_response  # local import to avoid LLM init at import
        record["judge"] = await judge_response(case, final_text, detected_language)

    return record


async def run_eval(
    cases_path: str | Path,
    out_dir: str | Path,
    *,
    judge: bool = True,
    agent_graph: Any | None = None,
) -> dict:
    cases_path = Path(cases_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard_path = out_dir / "scorecard.csv"

    if agent_graph is None:
        from app.agent.graph import agent_graph as default_graph
        agent_graph = default_graph

    cases = _read_cases(cases_path)
    run_id = now_run_id()
    rows: list[dict] = []
    records: list[dict] = []

    for case in cases:
        record = await _run_case(case, judge, agent_graph)
        records.append(record)
        judge_avg = ""
        if record.get("judge"):
            jvals = [v for v in (record["judge"].get(k) for k in
                                  ("warmth", "cultural_appropriateness", "helpfulness", "fluency"))
                     if v is not None]
            if jvals:
                judge_avg = f"{sum(jvals) / len(jvals):.2f}"
        passed_all = all(a["passed"] for a in record["assertions"])
        row = {
            "run_id": run_id,
            "timestamp": now_timestamp(),
            "case_id": case.get("id"),
            "category": case.get("category"),
            "language": record.get("detected_language"),
            "passed": str(passed_all).lower(),
            "deterministic_score": record.get("deterministic_score"),
            "judge_avg": judge_avg,
            "comments": record.get("judge", {}).get("comments", "") if record.get("judge") else "",
        }
        rows.append(row)
        append_row(scorecard_path, row)

    print(markdown_summary(rows))
    return {"run_id": run_id, "records": records, "rows": rows}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AstroAgent offline evaluation")
    parser.add_argument("--cases", type=Path, default=Path("backend/eval/golden_set.jsonl"))
    parser.add_argument("--out-dir", type=Path, default=Path("backend/eval"))
    parser.add_argument("--judge", action="store_true", help="Run the LLM judge as well")
    args = parser.parse_args(list(argv) if argv is not None else None)

    asyncio.run(run_eval(args.cases, args.out_dir, judge=args.judge))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run_eval", "main"]
