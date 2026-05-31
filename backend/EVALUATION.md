# AstroAgent Evaluation Harness

This is the contract for how we evaluate the agent. Agents are
non-deterministic — *"it worked when I tried it"* is not evidence. The
harness is a single command that produces a scorecard you can compare
across runs.

## How the rubric (EV01–EV06) maps to this repo

| Rubric | Where it lives |
|---|---|
| **EV01** Versioned 20–30 case golden set | `backend/eval/golden_set.jsonl` (30 cases, JSONL) |
| **EV02** Deterministic checks separated from judgment calls | `backend/app/eval/assertions.py` (deterministic) and `backend/app/eval/judge.py` (LLM judge). Per-case score is the fraction of deterministic assertions that pass; judge produces 1–5 scores on tone/quality only. |
| **EV03** Rubric-based judge with manual validation | `judge.py` uses a strict-JSON 1–5 rubric per axis with one retry. `judge_audit.py` samples 10 verdicts for manual spot-checking and reports exact / ±1 agreement rates. |
| **EV04** Cost, latency, reliability metrics | Per-case latency (ms), tool-call count, input/output tokens, and estimated USD cost are recorded for every case. Per-run aggregate prints p50 / p95 latency, total tokens, and total cost. |
| **EV05** Failure modes are explicit cases | The golden set has 4 graceful-failure cases (missing place, missing date, unknown person, invalid date) and 3 adversarial cases (fatalistic question, prompt injection, sensitive trigger). They assert the response stays warm, refuses to claim certainty, and never echoes the system prompt. |
| **EV06** One command + tracked over time | `uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge`. Each run appends a row to `eval/scorecard.csv` (per case) and `eval/runs.md` (per run aggregate). Compare adjacent rows in `runs.md` to spot regressions. |

## Running

```bash
# without the LLM judge (deterministic + metrics only — fastest)
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl

# with the judge (adds tone / cultural / fluency scores)
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

Outputs:

- `backend/eval/scorecard.csv` — one row per case appended per run.
- `backend/eval/runs.md` — one row per *run*, with the run-level aggregates.
- `backend/eval/last_run.json` — the full per-case snapshot of the most
  recent run (used by `judge_audit.py`).
- A markdown summary printed to stdout grouped by category, plus a
  run-level totals block.

## Scorecard columns

| Column | Meaning |
|---|---|
| `run_id` | Generated as `run-YYYYMMDDTHHMMSSZ` so runs sort lexicographically. |
| `case_id`, `category`, `language` | Identity of the case + detected response language. |
| `passed` | `true` only when every deterministic assertion passed. |
| `deterministic_score` | Fraction of deterministic assertions that passed (0.0–1.0). |
| `judge_avg` | Mean of the four judge axes (1–5) for this case, or empty when the judge was disabled or returned malformed JSON twice. |
| `latency_ms` | End-to-end wall-clock time for the full agent turn. |
| `tool_calls` | Number of tool invocations during the turn. |
| `input_tokens`, `output_tokens` | Sum of LLM token usage across all reasoning turns in the case. Read from `usage_metadata` on each `AIMessage`. |
| `est_cost_usd` | Approximate price using the rates in `scorecard.py`. Update those constants when model pricing changes. |
| `failure` | `true` when the agent raised an exception during the turn. |
| `comments` | Judge comment + failure reason, with API keys redacted. |

## Deterministic assertions

Every case is checked against this fixed set (see `assertions.py`):

- `tool_sequence_contains` — every tool listed in `expected_tools` was actually invoked.
- `chart_math` — when the run produced a chart, ascendant matches the expected sign (when given), all 9 grahas are present, planet count meets the case's `chart_planets_count`.
- `dasha_dates` — when the run produced a Vimshottari timeline, total span ≥ 120 years and an active maha-dasha exists.
- `guardrails` — none of the case's `must_not_contain` tokens appear in the response (used to enforce non-fatalistic language and refuse to leak the system prompt).
- `language_match` — detected response language matches `expected_language`.
- `step_budget` — total node visits ≤ the case's `step_budget`.

## Judge rubric

The judge scores four axes 1–5 each:

- **warmth** — does the response sound like a thoughtful astrologer? Cold or robotic = 1, present and caring = 5.
- **cultural_appropriateness** — Vedic/Indian framing, no astrology-as-superstition tone, Sanskrit terms used naturally.
- **helpfulness** — does it actually answer the seeker's question vs. dump tool data?
- **fluency** — clean prose in the expected language, no leftover JSON.

Judge prompt (in `judge.py`) demands strict JSON; we retry once with a stricter prompt before falling back to `null` scores and recording the failure mode in `comments`.

### Manual judge validation (EV03)

Audit 10 randomly sampled verdicts after a run:

```bash
uv run python -m app.eval.judge_audit --records backend/eval/last_run.json
```

It prints the question + response + judge scores and asks you to enter your
own 1–5 score per axis. At the end it reports:

- Exact agreement rate
- ±1 agreement rate

Treat the judge as evidence only when ±1 agreement is ≥ 80% on a fresh
audit. If it drops, retighten the rubric or replace the judge with a
stricter prompt.

## Adding new cases

Append a JSONL line to `backend/eval/golden_set.jsonl` with this schema:

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

To bootstrap a fresh scorecard, delete `backend/eval/scorecard.csv` and
`backend/eval/runs.md` between runs. The case file is the contract and is
versioned in git; never silently change a case's expected behaviour.

## Running the agent under eval mode

The runner imports `app.agent.graph.agent_graph` by default. External
services (Gemini, Qdrant, Supabase, Nominatim) **must** be mocked when the
harness runs against the live stack — there is no live network or live API
key expected. Tests should patch the graph and tool clients before
invoking `run_eval`.

## Categories in the starter set

- 10 valid charts (English, Hindi, Marathi, Gujarati, Tamil, Kannada inputs)
- 8 Vedic queries (dasha, sade sati, panchang, milan, muhurta, transits, sky, knowledge)
- 5 multilingual cases
- 4 graceful-failure cases (missing time, ambiguous place, unknown person, invalid date)
- 3 adversarial cases (fatalistic question, prompt injection, sensitive trigger)

Total: 30 cases. Distribution chosen so that no single category masks regressions in another.

## What "passing" means

We do not chase a perfect score. We chase **honest** scores that are
reproducible across runs. A useful eval signal looks like:

- Deterministic pass rate ≥ 0.90 across the suite.
- Judge avg ≥ 4.0 on warmth and cultural_appropriateness.
- p95 latency budget appropriate to the model (Gemini 2.5 Flash: ≤ 10s for tool-heavy turns).
- Failure rate ≤ 5%.

Drops below these on a fresh run are treated like a failing test and
investigated before merging.
