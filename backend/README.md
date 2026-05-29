# AstroAgent Backend

FastAPI + LangGraph backend for AstroAgent — an AI Vedic astrology
assistant powered by Google Gemini, Swiss Ephemeris, Supabase, and Qdrant.

## Stack

- **Python 3.12** with [uv](https://docs.astral.sh/uv/) for environment management
- **FastAPI** + WebSockets for the agent transport
- **LangGraph** for the agent state machine (router → reasoning → tool_executor → sensitivity → editor → response)
- **`langchain-google-genai`** to call `gemini-3-flash-preview`
- **`text-embedding-004`** for knowledge embeddings (Google)
- **`qdrant-client`** for vector retrieval
- **`pyswisseph`** for ephemeris (Lahiri ayanamsa)
- **Supabase** for relational storage (custom JWT cookie auth)

## Setup

```bash
# from repo root
cd backend

# install dependencies (creates .venv automatically)
uv sync

# copy and edit env
cp .env.example .env
# fill in GOOGLE_API_KEY, SUPABASE_*, QDRANT_*, JWT_SECRET, etc.
```

## Running

```bash
# dev server
uv run uvicorn app.main:app --reload --port 7860
```

The server exposes:

- `POST /auth/register`, `/auth/login`, `/auth/logout`, `GET /auth/me`
- `GET/POST/DELETE /api/profiles` — family vault
- `GET /api/conversations`, `GET /api/conversations/{id}/messages`
- `WS /ws/{session_id}` — main chat WebSocket (Phase 4 protocol)

### Database migration

Apply `supabase/migrations/001_initial_schema.sql` in the Supabase SQL editor.

### Knowledge base ingestion

```bash
# dry run (no API calls)
uv run python scripts/ingest_knowledge.py --dry-run

# real ingest into Qdrant
uv run python scripts/ingest_knowledge.py
```

The starter knowledge base is `knowledge_base/vedic_planets.md` (nine grahas).
Add more `.md` files to the same directory and rerun the script — chunk IDs
are deterministic, so the upsert is idempotent.

## Agent tools

Registered in `app/tools/__init__.py`:

| Tool | Purpose |
|------|---------|
| `compute_birth_chart` | Full Vedic chart from birth details |
| `geocode_place` | Place name → lat/lng/timezone |
| `compute_dasha_periods` | Vimshottari Maha + Antar dasha timeline |
| `compute_nakshatra_details` | Janma nakshatra deep analysis |
| `check_sade_sati` | Saturn-over-Moon Sade Sati / Ashtama Shani |
| `get_panchang` | Five limbs + Rahu Kaal / Yamaganda / Gulika / Abhijit |
| `knowledge_lookup` | Vector search over the curated KB |
| `kundali_milan` | Ashtakoota 8-fold compatibility + Mangal Dosha |
| `render_chart_svg` | Pure-Python SVG chart (South / North Indian) |
| `compute_muhurta` | Auspicious 30-minute window finder |
| `get_daily_transits` | Current transits relative to natal chart |
| `get_current_sky` | Generic current-sky snapshot |

## Evaluation

See [`EVALUATION.md`](./EVALUATION.md). To run the offline harness against
the 30-case golden set:

```bash
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

External services are expected to be mocked when the harness runs.

## Project layout

```
backend/
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── language_detector.py
│   │       ├── router.py
│   │       ├── reasoning.py
│   │       ├── tool_executor.py
│   │       ├── sensitivity.py
│   │       ├── editor.py
│   │       └── response.py
│   ├── api/                # REST routers (auth, profiles, conversations, panchang)
│   ├── auth/               # JWT + bcrypt + cookie helpers
│   ├── db/                 # supabase-py client + queries + pydantic models
│   ├── eval/               # offline harness (run, assertions, judge, scorecard)
│   ├── tools/              # all tool implementations + TOOL_REGISTRY
│   ├── config.py
│   └── main.py             # FastAPI app + /ws/{session_id}
├── eval/
│   └── golden_set.jsonl
├── knowledge_base/
│   └── vedic_planets.md
├── scripts/
│   └── ingest_knowledge.py
└── supabase/migrations/
```
