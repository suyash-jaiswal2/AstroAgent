# AstroAgent ✦ — Aradhana's Celestial Companion

> A conversational AI astrologer that computes real birth charts using the Swiss Ephemeris,
> reasons over live planetary data via a LangGraph agent, and responds with warmth and clarity.

![Aradhana Observatory UI](docs/screenshot_placeholder.png)

[![Eval Suite](https://github.com/suyash-jaiswal2/astroagent/actions/workflows/eval.yml/badge.svg)](https://github.com/suyash-jaiswal2/astroagent/actions/workflows/eval.yml)

---

## What It Does

AstroAgent is a full-stack agentic system. You describe your birth details — the agent computes your natal chart using real ephemeris data accurate to arcseconds, reasons over it using a ReAct loop, and responds with a warm, grounded astrological reading.

It is not a chatbot with canned responses. Every answer is assembled from real astronomical computation, a 112-document curated knowledge base, and an LLM reasoning loop bounded by an 8-step budget.

---

## Architecture

### LangGraph Agent Graph

![LangGraph Graph](docs/graph_diagram.png)
```
[START] → precheck → intent_router → reasoning ⇄ tool_node → response_formatter → [END]
↓ safety_block
format_error → [END]
```
**Nodes:**
- `precheck` — regex injection detection + `safety_block` routing (no LLM call)
- `intent_router` — lightweight Haiku call classifying into 10 intent labels
- `reasoning` — full ReAct loop (max 8 steps), Claude Haiku with all 9 tools bound
- `tool_node` — LangGraph `ToolNode` executing any of 9 tools
- `response_formatter` — safety disclaimer injection, eval metadata strip
- `format_error` — fixed safe deflection for injections

**State:** `AstroAgentState` carries messages, birth details, cached natal chart, intent, step count, and eval metadata across all nodes. The natal chart is computed once and cached forever in both state and SQLite.

### Tools (9 total)

| Tool | Purpose | Latency |
|---|---|---|
| `geocode_place` | Nominatim + timezonefinder — resolves place to lat/lon/tz | ~1.1s (rate limit) |
| `compute_birth_chart` | pyswisseph — tropical + sidereal charts, arcsecond accuracy | ~50ms |
| `get_daily_transits` | pyswisseph — current sky vs natal chart, aspects + moon phase | ~30ms |
| `knowledge_lookup` | ChromaDB + all-MiniLM-L6-v2 — retrieves from 112-doc knowledge base | ~80ms |
| `find_muhurta` | Scans 1440 half-hour slots, Vedic scoring, returns top 3 times | ~500ms |
| `compute_compatibility` | Ashtakoot (36-pt) + Western synastry — two-chart analysis | ~100ms |
| `detect_yogas` | 22 classical Vedic yoga formations with strength scoring | ~60ms |
| `get_panchang` | Five-limbed Hindu almanac: Tithi, Vara, Nakshatra, Yoga, Karana | ~40ms |
| `compute_dasha_timeline` | Vimshottari Dasha — 120-year life period timeline with Antardasha | ~30ms |

### Tech Stack

| Layer | Technology |
|---|---|
| LLM | Claude Haiku (primary), Gemini 2.0 Flash (eval judge) |
| Agent | LangGraph ≥ 0.2 |
| Ephemeris | pyswisseph (Swiss Ephemeris — same engine as Astro.com) |
| Vector DB | ChromaDB (local persistent) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 (local, free) |
| Backend | FastAPI + uvicorn (SSE streaming) |
| Database | SQLite via SQLAlchemy async |
| Frontend | React 18 + Vite 5 + TailwindCSS 3 |
| Animations | Framer Motion + pure CSS keyframes |
| Charts | D3.js v7 (natal chart wheel, dasha timeline) |

---

## Setup

### Prerequisites
- Python 3.11+
- Node 18+
- Git
- Microsoft C++ Build Tools (Windows only — for pyswisseph)

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/astroagent
cd astroagent
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Build the RAG knowledge base (one-time)
python knowledge_base/ingest.py

# Configure environment
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY and GOOGLE_API_KEY
```

### 3. Run Backend

```bash
uvicorn api.main:app --reload --port 8000
# Verify: http://localhost:8000/api/health → {"status":"ok"}
```

### 4. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# .env.local already has VITE_API_URL=http://localhost:8000
npm run dev
# Visit: http://localhost:5173
```

---

## Running Evaluations

```bash
# Make sure backend is running (separate terminal), then:
python eval/run_eval.py

# Single category:
python eval/run_eval.py --category chart_request_valid

# Dry-run (validate golden set format):
python eval/run_eval.py --dry-run

# Results saved to: eval/results/run_YYYY-MM-DD_HHMM.json
```

See `eval/results_log.md` for the version history of scorecard results.

---

## Project Structure
```
astroagent/
├── backend/
│   ├── agent/
│   │   ├── graph.py          # LangGraph graph assembly
│   │   ├── nodes.py          # All node functions (precheck, router, reasoning, formatter)
│   │   ├── state.py          # AstroAgentState TypedDict
│   │   └── tools/            # 9 tool implementations
│   ├── api/                  # FastAPI routes + SSE streaming
│   ├── db/                   # SQLAlchemy models + CRUD
│   └── knowledge_base/       # 112 markdown docs + ChromaDB + ingest pipeline
├── frontend/
│   └── src/
│       ├── components/       # Orb, Observatory, Chat, Chart components
│       ├── pages/            # Landing, BirthDetails, Chat, ChartExplorer, etc.
│       ├── hooks/            # useSSE, useOrbMood, usePanchang
│       └── store/            # Zustand session store
├── eval/
│   ├── golden_set.jsonl      # 30 versioned test cases
│   ├── run_eval.py           # One-command eval runner
│   └── results_log.md        # Historical scorecard
└── docs/
└── graph_diagram.png     # LangGraph visual
```
---

## Known Limitations

- Uranus/Neptune/Pluto interpretations are thin in the knowledge base (inner planets prioritized)
- Muhurta scanner uses 30-minute slots; sub-minute precision would require finer scanning
- Voice input is Chrome/Edge only (Web Speech API limitation)
- Render.com free tier has ~30s cold start after inactivity — frontend pings `/api/health` every 10min
- Compatibility requires manual entry of both charts (no link sharing)
- Pratyantar Dasha (sub-sub-period) not yet implemented
- Yoga strength uses simplified dignity scoring, not full Shadbala

---