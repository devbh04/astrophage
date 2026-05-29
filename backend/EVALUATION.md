# AstroAgent Evaluation Harness

The offline evaluation harness exercises the full LangGraph agent against a
curated 30-case golden set. It runs deterministic assertions on every case
and (optionally) an LLM judge for warmth, cultural appropriateness,
helpfulness, and language fluency.

All external services (Gemini, Qdrant, Supabase, Nominatim) **must** be
mocked when the harness runs — there is no live network or live API key
expected. The runner itself does not patch anything; tests should patch the
graph and tool clients before invoking `run_eval`.

## Running

```bash
# without the LLM judge
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl

# with the judge
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

Outputs:

- `backend/eval/scorecard.csv` — one row per case appended per run.
  Columns: `run_id, timestamp, case_id, category, language, passed,
  deterministic_score, judge_avg, comments`.
- A markdown summary printed to stdout grouped by category.

## Score interpretation

- `deterministic_score` is the fraction of deterministic assertions that
  passed (`tool_sequence_contains`, `chart_math`, `dasha_dates`,
  `guardrails`, `language_match`, `step_budget`).
- `judge_avg` is the arithmetic mean of the four judge axes (1..5) or empty
  when the judge was disabled or returned `null` on both attempts.
- `passed` is `true` only when every deterministic assertion passed for
  that case.

## Adding new cases

Append a JSONL line to `backend/eval/golden_set.jsonl` with the schema:

```json
{
  "id": "ev_031",
  "category": "vedic_query",
  "input": "...",
  "natal_chart": null,
  "expected_language": "en",
  "expected_tools": ["tool_name"],
  "assertions": {
    "must_contain": [],
    "must_not_contain": [],
    "step_budget": 5
  },
  "judge_rubric": ["warmth", "helpfulness"]
}
```

Run the harness; new rows will be appended to the scorecard. To bootstrap a
fresh scorecard, delete `backend/eval/scorecard.csv` between runs.

## Categories

The starter golden set covers:

- 10 valid charts (English, Hindi, Marathi, Gujarati, Tamil, Kannada inputs)
- 8 Vedic queries (dasha, sade sati, panchang, milan, muhurta, transits,
  sky, knowledge)
- 5 multilingual cases
- 4 graceful-failure cases (missing time, ambiguous place, unknown person,
  invalid date)
- 3 adversarial cases (fatalistic question, prompt injection, sensitive
  trigger)

Total: 30 cases.
