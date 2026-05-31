"""
Manual judge-validation helper.

EV03 in the evaluation rubric requires spot-checking at least 10 judge
verdicts against your own judgment and reporting the agreement rate.
This script samples 10 case records from the most recent eval run,
prints the question + assistant response + judge scores, and prompts
you to enter your own 1-5 score on each axis. It then reports
absolute and ±1-tolerance agreement rates.

Usage:
    uv run python -m app.eval.judge_audit --records backend/eval/last_run.json

The expected input is a JSON file containing the ``records`` list that
``run_eval`` returns. Generate one by importing ``run_eval`` from a
notebook or by capturing stdout.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Iterable


AXES = ("warmth", "cultural_appropriateness", "helpfulness", "fluency")


def _ask_score(label: str) -> int | None:
    while True:
        raw = input(f"  Your {label} (1-5, or 's' to skip): ").strip().lower()
        if raw in ("s", "skip", ""):
            return None
        try:
            n = int(raw)
            if 1 <= n <= 5:
                return n
        except ValueError:
            pass
        print("  Please enter 1, 2, 3, 4, 5, or 's'.")


def audit(records: list[dict], sample_size: int = 10, seed: int | None = 42) -> dict:
    judged = [r for r in records if r.get("judge") and any(
        r["judge"].get(ax) is not None for ax in AXES
    )]
    if not judged:
        print("No judge verdicts to audit.")
        return {"sampled": 0}

    rng = random.Random(seed)
    sample = rng.sample(judged, k=min(sample_size, len(judged)))

    exact = 0
    within_one = 0
    total = 0

    for i, rec in enumerate(sample, 1):
        print()
        print("=" * 78)
        print(f"Sample {i}/{len(sample)} — case_id={rec.get('case_id')}")
        print("-" * 78)
        print(f"Question: {rec.get('case_id')}")
        print(f"Response: {(rec.get('final_response') or '')[:600]}")
        print()
        print("Judge scores:")
        for ax in AXES:
            print(f"  {ax}: {rec['judge'].get(ax)}")
        print()
        for ax in AXES:
            judge_val = rec["judge"].get(ax)
            if judge_val is None:
                continue
            human_val = _ask_score(ax)
            if human_val is None:
                continue
            total += 1
            if human_val == judge_val:
                exact += 1
            if abs(human_val - judge_val) <= 1:
                within_one += 1

    if total == 0:
        return {"sampled": len(sample), "scored": 0}

    summary = {
        "sampled": len(sample),
        "scored": total,
        "exact_agreement": exact / total,
        "within_one": within_one / total,
    }
    print()
    print("=" * 78)
    print(f"Scored {total} judge verdicts across {len(sample)} cases")
    print(f"Exact agreement: {summary['exact_agreement']:.1%}")
    print(f"Agreement within ±1: {summary['within_one']:.1%}")
    return summary


def _load_records(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "records" in data:
        return list(data["records"])
    if isinstance(data, list):
        return data
    raise ValueError("Records file must be a JSON list or {records: [...]}.")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit LLM-judge verdicts manually.")
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(list(argv) if argv is not None else None)

    records = _load_records(args.records)
    audit(records, sample_size=args.sample_size, seed=args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["audit", "main"]
