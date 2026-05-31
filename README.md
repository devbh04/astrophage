<p align="center">
  <img src="https://astrophageai.vercel.app/logo.png" alt="Astrophage" width="140" />
</p>

<h1 align="center">Astrophage</h1>

<p align="center">
  <strong>AI Vedic Astrology Assistant — Voice, Chat, Multilingual</strong>
</p>

<p align="center">
  <a href="https://astrophageai.vercel.app"><img src="https://img.shields.io/badge/Live_Demo-astrophageai.vercel.app-8B5CF6?style=for-the-badge&logo=vercel" alt="Live Demo" /></a>
  <a href="https://youtube.com/watch?v=YOUR_VIDEO_ID"><img src="https://img.shields.io/badge/YouTube-Watch_Demo-FF0000?style=for-the-badge&logo=youtube" alt="YouTube" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?logo=next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?logo=google" />
  <img src="https://img.shields.io/badge/LangGraph-Agent-FF6F00" />
</p>

---

Astrophage is a full-stack AI astrologer that speaks 6 languages, computes real Vedic charts using Swiss Ephemeris, and converses in both text and voice. It remembers your birth details, your family, and your residence — so you never have to repeat yourself.

> **Try it live** → [astrophageai.vercel.app](https://astrophageai.vercel.app)

---

## Table of Contents

- [Features](#-features)
- [Agent Architecture](#-agent-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Evaluation System](#-evaluation-system)
- [Project Structure](#-project-structure)
- [Design Principles](#-design-principles)
- [Links](#-links)

---

## ✨ Features

### Chat Mode
- Conversational Vedic astrology with structured UI cards (charts, panchang, dasha timelines, compatibility scores)
- Markdown-rendered responses with tables, blockquotes, and warm astrologer tone
- Tool activity indicators streamed in real-time via WebSocket event bus
- Conversation persistence — cards and tool outputs survive page refresh

### Voice Mode
- Bidirectional audio with `gemini-live-2.5-flash-native-audio`
- AudioWorklet downsamples mic to 16 kHz PCM16; playback at 24 kHz gapless
- Visual voice orb with 64 radial bars driven by AnalyserNode
- Cards announce themselves ("Here is your panchang") before rendering
- Multi-turn sessions — no reconnect needed between questions

### Multilingual
- English, Hindi, Marathi, Gujarati, Tamil, Kannada
- Language directive injected into the freshest user-turn tokens (where Gemini weighs them highest)
- Sticky across turns — switch once in Settings, every reply follows

### Vedic Tools (12 tools, single registry)

| Tool | What it does |
|------|-------------|
| `compute_birth_chart` | Full sidereal Lahiri chart (9 grahas, 12 houses, nakshatras) |
| `render_chart_svg` | Pure-Python SVG in North or South Indian style |
| `compute_dasha_periods` | Vimshottari Maha + Antar + Pratyantar timeline |
| `compute_nakshatra_details` | Janma nakshatra deep-dive (deity, gana, yoni, nadi) |
| `check_sade_sati` | Saturn-over-Moon phase detection |
| `get_panchang` | Tithi, Nakshatra, Yoga, Karana, sunrise/sunset, Rahu Kaal |
| `kundali_milan` | Ashtakoota 8-fold compatibility + Mangal Dosha |
| `compute_muhurta` | Top 3 auspicious 30-minute windows for a purpose |
| `get_daily_transits` | Current transits relative to natal chart |
| `get_current_sky` | Generic planetary snapshot |
| `knowledge_lookup` | RAG over curated Vedic knowledge base (Qdrant + gemini-embedding-001) |
| `get_family_profile` | Look up saved family members by name or relationship |

### Family Vault
- Save birth profiles for family members
- `subject="mother"` on any chart tool renders their chart, not yours
- Kundali Milan resolves partner by name from the vault automatically

### Personalization
- Self birth details + residence saved in Settings
- Panchang always uses residence coords (never the place named in the message)
- Chart format preference (North/South Indian) persisted per user

---

## 🧠 Agent Architecture

The agent is a **LangGraph** state machine optimized for low latency (1–2 LLM calls per turn instead of 4–5 in the original design).

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER MESSAGE                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     REASONING       │ ← Gemini 2.5 Flash
                    │  (system prompt +   │   with 12 tools bound
                    │   tools + context)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              has tool_calls?       no tool_calls
                    │                     │
                    ▼                     ▼
         ┌──────────────────┐   ┌──────────────────┐
         │  TOOL EXECUTOR   │   │     RESPONSE     │
         │                  │   │  (draft → final) │
         │ • Runs tools via │   └────────┬─────────┘
         │   TOOL_REGISTRY  │            │
         │ • Emits cards    │            ▼
         │ • Emits SVG      │        END (reply
         │ • Streams events │         to user)
         └────────┬─────────┘
                  │
                  │ ToolMessages appended
                  │
                  └──────► back to REASONING
                           (loop until no more tool_calls)
```

**Key design choices:**

- **No separate router/editor/language-detector nodes** — the reasoning prompt handles all of this in a single LLM call, cutting latency from 15–30s to 3–8s.
- **Resolver-aware tool registry** — tools accept minimal args; the resolver fills in the user's chart, residence, birth details, and family vault from request-scoped ContextVars.
- **Subject resolution** — every chart tool accepts `subject="<name-or-relationship>"` so the model never needs to call `get_family_profile` first and thread chart dicts back.
- **Voice mode** uses the same `TOOL_REGISTRY` but with a separate Live API session (`gemini-live-2.5-flash-native-audio`) that handles VAD, speech recognition, reasoning, and voice synthesis natively.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Gemini 2.5 Flash (chat) · Gemini Live 2.5 Flash Native Audio (voice) |
| **Embeddings** | `gemini-embedding-001` (768-dim, L2-normalized) |
| **Agent Framework** | LangGraph + LangChain |
| **Backend** | FastAPI · Python 3.12 · uv |
| **Ephemeris** | pyswisseph (Lahiri ayanamsa) |
| **Vector DB** | Qdrant Cloud |
| **Relational DB** | Supabase (PostgreSQL) |
| **Auth** | Custom JWT + HttpOnly cookies (cross-origin via `?token=` fallback) |
| **Frontend** | Next.js 15 · React 19 · Tailwind CSS v4 · Zustand |
| **Voice UI** | Web Audio API · AudioWorklet · AnalyserNode |
| **Deployment** | Vercel (frontend) · HuggingFace Spaces / Cloud Run (backend) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 20+ and pnpm
- A Google Cloud project with Gemini API enabled (or a `GOOGLE_API_KEY`)
- Supabase project (free tier works)
- Qdrant Cloud cluster (free tier works)

### 1. Clone

```bash
git clone https://github.com/devbh04/astrophage.git
cd astrophage
```

### 2. Backend

```bash
cd backend

# Install all Python dependencies
uv sync

# Configure environment
cp .env.example .env
```

Fill in `.env`:

```env
GOOGLE_API_KEY=your-gemini-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-key
JWT_SECRET=any-strong-random-string
CORS_ORIGINS=http://localhost:3000
```

Run the database migration in Supabase SQL editor:
```sql
-- Paste contents of backend/supabase/migrations/001_initial_schema.sql
```

Ingest the knowledge base:
```bash
uv run python scripts/ingest_knowledge.py
```

Start the dev server:
```bash
uv run uvicorn app.main:app --reload --port 7860
```

### 3. Frontend

```bash
cd client
pnpm install
```

Create `client/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:7860
```

Start:
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000), register an account, add your birth details in Settings, and start chatting.

### 4. Production (optional)

For cross-origin cookie auth between Vercel frontend and a separate backend host:

```env
# In backend .env
COOKIE_CROSS_SITE=1
COOKIE_DOMAIN=.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

For GCP Vertex AI instead of API key:
```env
GCP_CREDENTIALS_PATH=/path/to/service-account.json
GCP_PROJECT=your-gcp-project
GCP_LOCATION=us-central1
```

---

## 🧪 Evaluation System

The eval harness is designed around the principle that **"it worked when I tried it" is not evidence**. It implements EV01–EV06 from the evaluation rubric.

### Run it

```bash
cd backend

# Deterministic assertions only (fast, no LLM cost)
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl

# Full suite with LLM judge
uv run python -m app.eval.run --cases backend/eval/golden_set.jsonl --judge
```

### What it measures

| Metric | How |
|--------|-----|
| **Tool correctness** | Did the expected tools fire? |
| **Chart math** | 9 grahas present, ascendant matches reference |
| **Guardrails** | No fatalistic/leaked-prompt tokens in response |
| **Language match** | Response language matches expected |
| **Step budget** | Node visits within the case's budget |
| **Latency** | Wall-clock ms per case (p50, p95 aggregated) |
| **Token usage** | Input + output tokens from `usage_metadata` |
| **Cost** | Estimated USD per case |
| **Failure rate** | Exceptions during agent execution |
| **Tone (judge)** | Warmth, cultural appropriateness, helpfulness, fluency (1–5 each) |

### Outputs

- `eval/scorecard.csv` — one row per case, appended each run
- `eval/runs.md` — one row per run (aggregates for drift detection)
- `eval/last_run.json` — full snapshot for manual judge audit

### Judge validation

```bash
# Spot-check 10 random judge verdicts against your own scoring
uv run python -m app.eval.judge_audit --records backend/eval/last_run.json
```

Reports exact agreement and ±1 agreement rates. Trust the judge only when ±1 agreement is ≥ 80%.

### Golden set coverage (30 cases)

- 10 valid charts (6 languages)
- 8 Vedic queries (dasha, sade sati, panchang, milan, muhurta, transits, sky, knowledge)
- 5 multilingual cases
- 4 graceful-failure cases
- 3 adversarial cases

Full documentation: [`backend/EVALUATION.md`](./backend/EVALUATION.md)

---

## 📁 Project Structure

```
astrophage/
├── backend/
│   ├── app/
│   │   ├── agent/                 # LangGraph state machine
│   │   │   ├── graph.py           # reasoning ⟷ tool_executor → response
│   │   │   ├── state.py           # AgentState TypedDict
│   │   │   ├── _user_context.py   # Request-scoped ContextVars
│   │   │   ├── _llm_factory.py    # Vertex AI / API key auto-detection
│   │   │   ├── _event_bus.py      # In-memory pub/sub for tool events
│   │   │   └── nodes/
│   │   │       ├── reasoning.py   # Main LLM node (tools bound)
│   │   │       ├── tool_executor.py
│   │   │       └── response.py
│   │   ├── tools/                 # 12 Vedic tools
│   │   │   ├── __init__.py        # TOOL_REGISTRY
│   │   │   ├── _resolvers.py      # Single source of truth for defaults
│   │   │   ├── _langchain_tools.py # @tool wrappers for LangChain
│   │   │   ├── birth_chart.py     # Swiss Ephemeris computation
│   │   │   ├── chart_svg.py       # Pure-Python SVG renderer
│   │   │   ├── dasha.py           # Vimshottari algorithm
│   │   │   └── ...                # panchang, muhurta, nakshatra, etc.
│   │   ├── api/
│   │   │   ├── chat.py            # POST /api/chat (HTTP agent turn)
│   │   │   ├── voice.py           # WS /ws/voice (Gemini Live bridge)
│   │   │   ├── conversations.py   # CRUD for chat history
│   │   │   └── profiles.py        # Family vault API
│   │   ├── auth/                  # JWT + bcrypt + cookie auth
│   │   ├── db/                    # Supabase client + queries
│   │   ├── eval/                  # Evaluation harness
│   │   │   ├── run.py             # One-command runner
│   │   │   ├── assertions.py      # Deterministic checks
│   │   │   ├── judge.py           # LLM-as-judge (rubric-based)
│   │   │   ├── scorecard.py       # CSV + markdown + cost estimation
│   │   │   └── judge_audit.py     # Manual judge validation
│   │   └── main.py               # FastAPI app entry point
│   ├── eval/golden_set.jsonl      # 30 versioned test cases
│   ├── knowledge_base/            # Curated Vedic markdown (chunked → Qdrant)
│   ├── scripts/ingest_knowledge.py
│   ├── EVALUATION.md
│   └── pyproject.toml
├── client/
│   ├── app/(app)/
│   │   ├── chat/page.tsx          # Main chat interface
│   │   ├── family/                # Family vault pages
│   │   ├── calendar/page.tsx      # Panchang calendar
│   │   ├── settings/page.tsx      # Self birth + residence
│   │   └── layout.tsx             # App shell + topbar + drawer
│   ├── components/
│   │   ├── cards/                 # 12 structured card components
│   │   ├── voice/VoiceModal.tsx   # Voice orb + card stack
│   │   └── chat/                  # MarkdownProse + tool indicators
│   ├── lib/
│   │   ├── store.ts              # Zustand (user, profiles, language)
│   │   └── api.ts                # HTTP + WS client helpers
│   └── package.json
├── astrophage-be/                 # Deploy mirror (HuggingFace Spaces)
└── README.md                      # You are here
```

---

## 🎯 Design Principles

**For the seeker:**
- No fatalism — placements are tendencies, not destiny
- Cultural authenticity — Sanskrit terms used naturally, Indian framing
- Warmth over raw data — interpret, don't regurgitate
- Privacy by design — data stays in your Supabase instance

**For the developer:**
- Resolver-aware tool registry — one source of truth, no mismatch between what the LLM sees and what runs
- Request-scoped ContextVars — clean separation of HTTP context from tool logic
- Voice model constraints — tools accept minimal args so the model never reads lat/lng aloud
- Defensive caps — 4000-char reply limit, graceful error dicts, frontend guards

**For the evaluator:**
- Honest scores over perfect scores — reproducible metrics, not cherry-picked demos
- Cost and latency are first-class — correct but slow is a regression
- Failure modes tested on purpose — graceful failure is a feature
- Judge validation required — unvalidated judge is not evidence

---

## 🔗 Links

| | |
|---|---|
| **Live Demo** | [astrophageai.vercel.app](https://astrophageai.vercel.app) |
| **YouTube Demo** | [Watch the walkthrough](https://youtube.com/watch?v=YOUR_VIDEO_ID) |
| **GitHub** | [github.com/devbh04/astrophage](https://github.com/devbh04/astrophage) |

---

<p align="center">
  <em>Built for seekers, by a seeker.</em>
</p>
