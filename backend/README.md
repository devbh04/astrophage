# AstroAgent Backend

<div align="center">

**FastAPI + LangGraph backend for AI Vedic astrology**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-FF6B6B?style=for-the-badge)](https://langchain.com/langgraph)
[![Swiss Ephemeris](https://img.shields.io/badge/Swiss_Ephemeris-Astronomy-4ECDC4?style=for-the-badge)](https://www.astro.com/swisseph/)

*12 Vedic tools • 6-language agent • Voice mode • Evaluation harness*

</div>

## 🏗️ Architecture Overview

```
backend/
├── app/
│   ├── agent/                 # LangGraph state machine
│   │   ├── graph.py          # Compiled: language → router → reasoning → sensitivity → editor
│   │   ├── nodes/            # 7 specialized nodes
│   │   │   ├── language_detector.py  # Unicode script → language code
│   │   │   ├── router.py             # needs_tool? → reasoning : response
│   │   │   ├── reasoning.py          # Gemini 2.5 Flash with tool-calling
│   │   │   ├── tool_executor.py      # TOOL_REGISTRY dispatcher
│   │   │   ├── sensitivity.py        # Health/death/finance classifier
│   │   │   ├── editor.py             # Second-pass polish
│   │   │   └── response.py           # Final message assembly
│   │   ├── _user_context.py  # ContextVar binding (user_id, natal_chart, family_rows, etc.)
│   │   └── _llm_factory.py   # Gemini client (Vertex AI + dev API)
│   ├── tools/                # 12 Vedic tools + registry
│   │   ├── __init__.py       # TOOL_REGISTRY export
│   │   ├── _resolvers.py     # SINGLE SOURCE OF TRUTH - default filling
│   │   ├── _langchain_tools.py  # @tool wrappers for LC_TOOLS
│   │   ├── birth_chart.py    # compute_birth_chart (Phase 1)
│   │   ├── geocode.py        # geocode_place (Phase 1)
│   │   ├── dasha.py          # Vimshottari Dasha timeline
│   │   ├── nakshatra.py      # Janma Nakshatra deep analysis
│   │   ├── sade_sati.py      # Saturn-over-Moon phases
│   │   ├── panchang.py       # Five limbs + Rahu Kaal/Yamaganda
│   │   ├── knowledge_lookup.py  # Vector search over curated KB
│   │   ├── kundali_milan.py  # Ashtakoota 8-fold compatibility
│   │   ├── chart_svg.py      # Pure-Python SVG (South/North Indian)
│   │   ├── muhurta.py        # Auspicious window finder
│   │   ├── daily_transits.py # Current transits vs natal
│   │   ├── current_sky.py    # Real-time planetary positions
│   │   └── family_profile.py # Family vault lookup
│   ├── api/                  # HTTP + WebSocket endpoints
│   │   ├── chat.py           # POST /api/chat (sensitive turn gating)
│   │   ├── voice.py          # /ws/voice → gemini-live-2.5-flash-native-audio
│   │   ├── profiles.py       # Family vault CRUD
│   │   ├── conversations.py  # Conversation history
│   │   ├── panchang.py       # GET /api/panchang (standalone)
│   │   └── tools.py          # GET /api/tools (registry inspection)
│   ├── eval/                 # Evaluation harness (EV01–EV06)
│   │   ├── run.py            # One-command runner
│   │   ├── scorecard.py      # CSV + markdown aggregation
│   │   ├── judge.py          # LLM-as-judge with 1–5 rubric
│   │   ├── judge_audit.py    # Manual spot-check validation
│   │   └── assertions.py     # Deterministic checks
│   ├── auth/                 # JWT cookie auth
│   ├── db/                   # Supabase client + queries
│   └── main.py               # FastAPI app + /ws/{session_id}
├── eval/
│   └── golden_set.jsonl      # 30 test cases
├── knowledge_base/
│   └── vedic_planets.md      # Starter corpus (9 grahas)
├── scripts/
│   └── ingest_knowledge.py   # Chunk → embed → Qdrant
└── supabase/migrations/
    └── 001_initial_schema.sql
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# From repo root
cd backend

# Install dependencies (uv creates .venv automatically)
uv sync

# Copy and configure environment
cp .env.example .env
```

**Required `.env` variables:**
```bash
# Google AI (Gemini 2.5 Flash + text-embedding-004)
GOOGLE_API_KEY=your_key_here

# OR for Vertex AI:
USE_VERTEX=1
GCP_PROJECT=your-project
GCP_LOCATION=us-central1
GCP_CREDENTIALS_PATH=/path/to/credentials.json

# Supabase (PostgreSQL + auth)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Qdrant (vector search)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_key

# Application
JWT_SECRET=strong_random_string_here
COOKIE_CROSS_SITE=1  # For production cross-origin
# COOKIE_DOMAIN=.example.com  # Optional for production
```

### 2. Database Migration
In your Supabase SQL editor, paste the contents of:
```bash
backend/supabase/migrations/001_initial_schema.sql
```

This creates:
- `users` table with `residence_*` columns
- `birth_profiles` table for family vault
- `conversations` and `messages` tables
- JWT-compatible RLS policies

### 3. Knowledge Base Ingestion
```bash
# Dry run first (prints chunk counts, no API calls)
uv run python scripts/ingest_knowledge.py --dry-run

# Real ingest (idempotent - reruns produce identical point IDs)
uv run python scripts/ingest_knowledge.py
```

The starter corpus is `knowledge_base/vedic_planets.md` (nine grahas). Add more `.md` files to the same directory and rerun the script.

### 4. Run Development Server
```bash
uv run uvicorn app.main:app --reload --port 7860
```

## 🔧 API Endpoints

### HTTP REST
- `POST /auth/register`, `/auth/login`, `/auth/logout`, `GET /auth/me`
- `GET/POST/DELETE /api/profiles` - Family vault CRUD
- `GET /api/conversations`, `GET /api/conversations/{id}/messages`
- `POST /api/chat` - Single-turn agent invocation
- `POST /api/chat/{id}/confirm` - Resume sensitive turn
- `GET /api/panchang?date=...` - Standalone panchang

### WebSockets
- `WS /ws/{session_id}` - Main chat protocol (Phase 4)
  - Frames: `tool_start`, `tool_end`, `token`, `chart_svg`, `structured_card`, `confirmation_required`, `done`, `error`
- `WS /ws/voice` - Voice mode bridge to Gemini Live
  - Binary: 16kHz PCM16 in → 24kHz PCM16 out
  - Control: `tool_start`, `tool_end`, `structured_card`, `chart_svg`, `input_transcription`, `output_transcription`, `turn_complete`

## 🛠️ Tool Registry & Resolvers

**Single source of truth:** `app/tools/_resolvers.py`

Every tool has a `_resolved` wrapper that:
1. Fills missing args from request-scoped ContextVars (`_user_context.py`)
2. Maps `subject="<name-or-relationship>"` to family vault charts
3. Provides sensible defaults (today's date, residence coords, seeker's chart)
4. Handles async/sync dispatch transparently

**Two consumers:**
- `TOOL_REGISTRY` (used by `tool_executor_node`)
- `LC_TOOLS` (bound to Gemini for tool-calling)

**Example resolver pattern:**
```python
def compute_dasha_periods_resolved(
    natal_chart: dict | None = None,
    birth_date: str | None = None,
    birth_time: str | None = None,
    timezone: str | None = None,
    levels: int = 2,
    subject: str | None = None,  # ← NEW: "mother", "Riya", "self"
) -> dict:
    payload = resolve_subject(subject) or {}
    chart = _subject_chart(subject, natal_chart)  # ← picks family member's chart
    return _compute_dasha_periods(
        chart,
        birth_date or payload.get("birth_date") or ...,
        # ... defaults filled
    )
```

## 🧪 Evaluation Harness

**Implements EV01–EV06:**
- **EV01** Golden set: `eval/golden_set.jsonl` (30 cases)
- **EV02** Deterministic vs judge: `assertions.py` + `judge.py`
- **EV03** Rubric-based judge: 1–5 scores with manual validation
- **EV04** Cost/latency/reliability: per-case metrics in scorecard
- **EV05** Failure modes: 4 graceful + 3 adversarial cases
- **EV06** One command + tracked: `runs.md` for drift detection

**Run:**
```bash
# Without judge (deterministic + metrics only)
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl

# With judge (adds tone/quality scores)
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

**Outputs:**
- `eval/scorecard.csv` - Per-case rows (latency_ms, tool_calls, input_tokens, output_tokens, est_cost_usd, failure)
- `eval/runs.md` - Run-level aggregates (p50/p95 latency, total tokens, cost)
- `eval/last_run.json` - Full snapshot for `judge_audit.py`

**Manual judge validation:**
```bash
uv run python -m app.eval.judge_audit --records backend/eval/last_run.json
```

See [`EVALUATION.md`](./EVALUATION.md) for complete documentation.

## 🎤 Voice Mode

**Protocol:** `/ws/voice` bridges browser ↔ `gemini-live-2.5-flash-native-audio`

**Key constraints:**
- Voice models avoid reading floats (lat/lng) aloud
- Tools accept minimal args (often zero - defaults filled)
- `kundali_milan(girl_chart="Priya")` - name only, never dates/addresses
- Knowledge cards hidden (model summarizes inline)

**System prompt** mirrors text reasoning but adds:
- "Speak naturally, unhurried, like a thoughtful family astrologer"
- "Keep each turn 2–6 sentences. Never recite long lists aloud"
- "After a tool runs, briefly explain what it tells the seeker"

## 🔐 Security & Production

### Cross-Origin Cookies
For production with separate frontend/backend domains:
```bash
COOKIE_CROSS_SITE=1
COOKIE_DOMAIN=.example.com  # Optional, for subdomain sharing
```

**Requirements:**
- Backend must be HTTPS
- Frontend must be same-site or configured CORS
- `secure=True` cookies (auto-set by FastAPI when `COOKIE_CROSS_SITE=1`)

### Secret Management
- API keys in `.env` (never committed)
- `scorecard.py` redacts `GOOGLE_API_KEY`, `QDRANT_API_KEY`, `JWT_SECRET` from logs
- Supabase RLS ensures user data isolation

### Rate Limiting
- Consider adding `slowapi` or `fastapi-limiter` for production
- Gemini 2.5 Flash: 60 RPM default, 429 after 65 seconds wait

## 📚 Development Notes

### Adding New Tools
1. Implement in `app/tools/` with `_tool()` function
2. Add `_tool_resolved()` wrapper in `_resolvers.py`
3. Register in `TOOL_REGISTRY` (`app/tools/__init__.py`)
4. Add `@tool` wrapper in `_langchain_tools.py` (optional)
5. Update voice declarations (`app/api/voice.py`)
6. Add to reasoning prompt (`app/agent/nodes/reasoning.py`)
7. Create frontend card component (`client/components/cards/`)

### ContextVar Lifecycle
```python
# In request handler:
with set_request_context(
    user_id=user["id"],
    natal_chart=natal_chart,
    chart_format=user.get("chart_format"),
    residence=residence_payload,
    self_birth=self_birth_payload,
    family_rows=family_rows,  # ← for subject="mother" resolution
):
    result = await agent_graph.ainvoke(...)

# In tool resolver:
def some_tool_resolved(subject: str | None = None):
    payload = resolve_subject(subject)  # ← uses _current_family_rows
    chart = payload.get("chart") if payload else get_current_natal_chart()
```

### Testing
```bash
# Run all tests (external services mocked)
uv run pytest

# Run specific test file
uv run pytest backend/tests/tools/test_dasha.py -v

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/astrophage/issues)
- **Documentation**: See top-level [`README.md`](../README.md) for project overview
- **Evaluation**: [`EVALUATION.md`](./EVALUATION.md) for harness details

---

<div align="center">

*May your code compile and your charts be accurate* ✨

</div>
