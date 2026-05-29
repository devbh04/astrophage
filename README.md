# Astrophage

AstroAgent is an AI Vedic astrology assistant: a FastAPI + LangGraph backend
calling Google Gemini and Swiss Ephemeris, paired with a Next.js 16 client.

## Repo layout

```
astrophage/
├── backend/    # FastAPI + LangGraph agent (Python 3.12, uv)
├── client/     # Next.js 16 frontend (Tailwind v4 + shadcn/ui, pnpm)
```

## Run guide

### 1. Backend

```bash
cd backend
uv sync
cp .env.example .env       # fill in GOOGLE_API_KEY, SUPABASE_*, QDRANT_*, JWT_SECRET
uv run uvicorn app.main:app --reload --port 7860
```

Apply the Supabase migration once:

```bash
# in the Supabase SQL editor, paste the contents of:
backend/supabase/migrations/001_initial_schema.sql
```

Ingest the starter knowledge base (idempotent):

```bash
cd backend
uv run python scripts/ingest_knowledge.py
```

### 2. Client

```bash
cd client
pnpm install
pnpm dev   # http://localhost:3000
```

Set the `NEXT_PUBLIC_API_URL` env var to point at the backend if it isn't
running on `http://localhost:7860`.

### 3. Evaluation

The offline evaluation harness exercises the agent against a 30-case golden
set. All external services must be mocked at run time.

```bash
cd backend
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

See [`backend/EVALUATION.md`](./backend/EVALUATION.md) for scorecard format
and how to add new cases.

