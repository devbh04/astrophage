# AstroAgent 🌟

<div align="center">

<img src="https://astrophageai.vercel.app/logo.png" alt="AstroAgent Logo" width="200" height="200" />

**An AI Vedic Astrology Assistant with Voice & Multilingual Support**

[![Live Demo](https://img.shields.io/badge/Live_Demo-AstrophageAI-8B5CF6?style=for-the-badge&logo=vercel)](https://astrophageai.vercel.app)
[![YouTube Demo](https://img.shields.io/badge/YouTube_Demo-Watch-FF0000?style=for-the-badge&logo=youtube)](https://youtube.com/watch?v=YOUR_VIDEO_ID)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

*Speak with an AI astrologer in 6 languages • Compute Vedic charts • Find auspicious moments • Check compatibility*

</div>

## ✨ Features

### 🤖 **Intelligent Agent**
- **LangGraph-powered** state machine with language detection, sensitivity filtering, and response editing
- **Multilingual support** (English, Hindi, Marathi, Gujarati, Tamil, Kannada) with automatic detection
- **Context-aware tools** that remember your birth details, residence, and family members
- **Warm, culturally-appropriate** responses tuned by a second-pass editor

### 🎤 **Voice Mode**
- **Bidirectional voice chat** with `gemini-live-2.5-flash-native-audio`
- **Real-time audio processing** (16kHz input → 24kHz output)
- **Visual voice orb** with 64 radial bars driven by AnalyserNode
- **Seamless tool integration** - ask aloud, see cards appear

### 🔮 **Vedic Tools Suite**
| Tool | Purpose | Example |
|------|---------|---------|
| **Birth Chart** | Full Vedic chart from birth details | "Show my chart" |
| **Vimshottari Dasha** | Planetary period timeline (120+ years) | "What's my current dasha?" |
| **Janma Nakshatra** | Birth star deep analysis | "Tell me about my nakshatra" |
| **Sade Sati** | Saturn-over-Moon phases | "Am I in Sade Sati?" |
| **Panchang** | Five limbs + Rahu Kaal/Yamaganda | "Today's panchang" |
| **Kundali Milan** | Ashtakoota 8-fold compatibility | "Check compatibility with Priya" |
| **Muhurta Finder** | Auspicious 30-minute windows | "Find wedding muhurta next week" |
| **Daily Transits** | Current transits vs natal chart | "Today's transits for me" |
| **Current Sky** | Real-time planetary positions | "What's in the sky now?" |
| **Knowledge Lookup** | Curated Vedic knowledge base | "Tell me about Saturn's nature" |

### 👨‍👩‍👧‍👦 **Family Vault**
- **Save profiles** for family members (mother, father, spouse, children)
- **Automatic chart resolution** - "show my mother's chart" just works
- **Subject-aware tools** - all chart tools accept `subject="<name-or-relationship>"`
- **Residence-aware** - panchang always uses your current residence coords

### 📊 **Professional Evaluation**
- **30-case golden set** covering valid charts, Vedic queries, multilingual cases, graceful failures, adversarial prompts
- **Deterministic assertions** + LLM-as-judge with 1–5 rubric
- **Cost/latency/reliability metrics** (p50/p95 latency, token counts, USD cost, failure rate)
- **One-command runner** with scorecard CSV + run history markdown

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend

# Install dependencies (uv creates .venv automatically)
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your:
# - GOOGLE_API_KEY (Gemini 2.5 Flash + text-embedding-004)
# - SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET
# - QDRANT_URL, QDRANT_API_KEY
# - JWT_SECRET (any strong random string)

# Run dev server
uv run uvicorn app.main:app --reload --port 7860
```

### 2. Database Migration
In your Supabase SQL editor, paste:
```sql
-- From: backend/supabase/migrations/001_initial_schema.sql
-- Creates users, birth_profiles, conversations, messages tables
-- Adds residence_* columns to users table
```

### 3. Knowledge Base Ingestion
```bash
# Dry run first
uv run python scripts/ingest_knowledge.py --dry-run

# Real ingest (idempotent - reruns are safe)
uv run python scripts/ingest_knowledge.py
```

### 4. Frontend Setup
```bash
cd client

# Install dependencies
pnpm install

# Run dev server (defaults to http://localhost:3000)
pnpm dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:7860` in `client/.env.local` if needed.

## 🏗️ Architecture

```
astrophage/
├── backend/                    # FastAPI + LangGraph
│   ├── app/
│   │   ├── agent/             # LangGraph state machine
│   │   │   ├── graph.py       # Compiled graph (language → router → reasoning → sensitivity → editor)
│   │   │   ├── nodes/         # Individual nodes
│   │   │   └── _user_context.py # Request-scoped ContextVars
│   │   ├── tools/             # 12 Vedic tools + TOOL_REGISTRY
│   │   │   └── _resolvers.py  # Single source of truth for tool defaults
│   │   ├── api/               # REST + WebSocket endpoints
│   │   │   ├── chat.py        # HTTP chat API
│   │   │   └── voice.py       # /ws/voice bridge to Gemini Live
│   │   ├── eval/              # Evaluation harness
│   │   │   ├── run.py         # One-command runner
│   │   │   ├── scorecard.py   # CSV + markdown aggregation
│   │   │   └── judge.py       # LLM-as-judge with rubric
│   │   └── main.py            # FastAPI app + /ws/{session_id}
│   ├── eval/golden_set.jsonl  # 30 test cases
│   └── knowledge_base/        # Curated Vedic markdown
├── client/                     # Next.js 16 + Tailwind v4
│   ├── app/(app)/             # App router pages
│   │   ├── chat/              # Main chat interface
│   │   ├── family/            # Family vault management
│   │   ├── calendar/          # Panchang calendar view
│   │   └── settings/          # Self birth + residence
│   ├── components/
│   │   ├── cards/             # 12 structured card types
│   │   ├── voice/             # VoiceModal + VoiceOrb
│   │   └── chat/              # MarkdownProse + message bubbles
│   └── lib/store.ts           # Zustand persistence
└── README.md                  # This file
```

## 🧪 Evaluation System

AstroAgent ships with a production-grade evaluation harness that implements **EV01–EV06**:

```bash
# Run the full suite (deterministic + judge)
cd backend
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

**Outputs:**
- `backend/eval/scorecard.csv` - Per-case metrics (latency, tokens, cost, pass/fail)
- `backend/eval/runs.md` - Run-level aggregates for drift detection
- `backend/eval/last_run.json` - Full snapshot for manual audit

**Scorecard columns:** `run_id`, `case_id`, `category`, `language`, `passed`, `deterministic_score`, `judge_avg`, `latency_ms`, `tool_calls`, `input_tokens`, `output_tokens`, `est_cost_usd`, `failure`, `comments`

**Golden set distribution:**
- 10 valid charts (6 languages)
- 8 Vedic queries (dasha, sade sati, panchang, milan, muhurta, transits, sky, knowledge)
- 5 multilingual cases
- 4 graceful-failure cases (missing time, ambiguous place, unknown person, invalid date)
- 3 adversarial cases (fatalistic question, prompt injection, sensitive trigger)

See [`backend/EVALUATION.md`](./backend/EVALUATION.md) for complete documentation.

## 🎯 Design Principles

### For the Seeker
- **No fatalism** - placements are tendencies, not destiny
- **Cultural authenticity** - Sanskrit terms used naturally, Indian framing
- **Warmth over accuracy** - a caring astrologer first, calculator second
- **Privacy by design** - user data never leaves your Supabase instance

### For the Developer
- **Resolver-aware tool registry** - single source of truth in `_resolvers.py`
- **Request-scoped ContextVars** - clean separation of HTTP context from tool logic
- **Voice model constraints** - tools accept minimal args (no lat/lng reading aloud)
- **Defensive caps** - 4000-character reply limit, graceful error handling

### For the Evaluator
- **Honest scores over perfect scores** - reproducible metrics, not cherry-picked demos
- **Cost/latency as first-class metrics** - correct but slow is a regression
- **Failure modes tested on purpose** - graceful failure is a feature
- **Judge validation required** - spot-check 10 verdicts, report ±1 agreement rate

## 📞 Contact & Links

- **Portfolio**: [devbhangale.vercel.app](https://devbhangale.vercel.app)
- **Live Demo**: [astrophageai.vercel.app](https://astrophageai.vercel.app)
- **YouTube Demo**: [Watch the walkthrough](https://youtube.com/watch?v=YOUR_VIDEO_ID)
- **GitHub**: [github.com/devbh04/astrophage](https://github.com/devbh04/astrophage)


---

<div align="center">

*Built with care for seekers everywhere* ✨

</div>
