# AstroAgent ✦ — Aradhana's Celestial Companion

> A conversational AI Vedic astrologer that computes real birth charts using the Swiss Ephemeris,
> reasons over live planetary data via a LangGraph agent, and responds with warmth, clarity, and beautiful legibility.

---

## ✦ Overview

AstroAgent is a full-stack, state-of-the-art agentic system designed to deliver precise Vedic and Western astrological insights. By combining precise mathematical ephemeris calculations with an advanced ReAct reasoning loop, it provides highly structured, individualized, and legally compliant readings. 

Rather than relying on canned responses or simple LLM prompts, AstroAgent dynamically computes your exact birth chart (to the arcsecond), maps Vimshottari Dashas, scans for 22 classical Vedic yoga formations, and cross-references a 112-document curated knowledge base to answer complex life, career, and muhurta questions.

---

## 🪐 Architecture & Cognition

### LangGraph Agent State Machine

AstroAgent is orchestrated using a deterministic **LangGraph State Graph** that bounds the agent's reasoning within a strict 8-step budget.

```
                  [START]
                     │
                     ▼
                 precheck ─────────(prompt injection)──────► format_error ──► [END]
                     │
                     ▼
               intent_router
                     │
                     ▼
        ┌──────► reasoning ◄──────┐
        │            │            │
  (tool output)  (tool call)  (tool loop)
        │            ▼            │
        └─────── tool_node ───────┘
                     │
             (reasoning complete)
                     │
                     ▼
             response_formatter ──► [END]
```

#### Graph Nodes:
* **`precheck`** — Validates query safety and screens for prompt injection blocklists (executed locally without LLM overhead).
* **`intent_router`** — A high-speed classifier that categorizes queries into 10 intent profiles (e.g. `chart_request`, `compatibility`, `panchang_inquiry`).
* **`reasoning`** — A ReAct loop (max 8 steps) using tool-calling to resolve geocoding, planet calculations, RAG vector searches, and Vedic yoga detections.
* **`tool_node`** — Executes any of the 9 high-precision computational tools.
* **`response_formatter`** — Wraps final text with essential legal disclaimers, strips internal evaluation metadata, and formats structure.
* **`format_error`** — Returns safe, standardized deflections for injection threats.

---

## 🛠️ The 9 Computational Tools

AstroAgent is equipped with 9 mathematical tools to fetch accurate real-time data:

| Tool Name | Engine & Mechanism | Latency |
|:---|:---|:---|
| **`geocode_place`** | Nominatim + timezonefinder — Resolves locations to lat/lon/tz | ~1.1s (network) |
| **`compute_birth_chart`** | `pyswisseph` (Swiss Ephemeris) — Tropical & Sidereal planetary degrees | ~50ms (local) |
| **`get_daily_transits`** | `pyswisseph` — Renders planet transits vs natal degrees with synastry aspects | ~30ms (local) |
| **`knowledge_lookup`** | ChromaDB + `all-MiniLM-L6-v2` — Performs RAG search over 112 Vedic docs | ~80ms (local) |
| **`find_muhurta`** | Scans 1440 half-hour daily increments, calculating composite Panchang scores | ~500ms (local) |
| **`compute_compatibility`** | Ashtakoot (36-point) + Western Synastry — Dual chart evaluation | ~100ms (local) |
| **`detect_yogas`** | Scans for 22 classical yogas (e.g., Pancha Mahapurusha, Raja Yogas) | ~60ms (local) |
| **`get_panchang`** | Computes active Tithi, Vara, Nakshatra, Yoga, and Karana for any location | ~40ms (local) |
| **`compute_dasha_timeline`** | Vimshottari Dasha — Traces 120-year hierarchical periods down to Antardashas | ~30ms (local) |

---

## ⚡ Technical Stack

AstroAgent is built on a modern, decoupled developer stack:

* **Primary LLM**: **Gemini 3.1 Flash-Lite** (`ChatGoogleGenerativeAI`) for lightning-fast tool selection and reasoning.
* **LLM Fallback**: **Groq Llama-3.1-8B-Instant** (`ChatGroq`) which automatically binds and handles requests if Gemini experiences rate-limiting or network issues.
* **Agent Framework**: LangGraph ≥ 0.2
* **Vector DB**: Local persistent **ChromaDB** with sentence-transformers `all-MiniLM-L6-v2` local embeddings.
* **Astronomical Engine**: **Swiss Ephemeris** (via `pyswisseph` binding) — identical mathematical precision used by professional sites like Astro.com.
* **REST Backend**: **FastAPI** + Uvicorn. Calls are served via highly stable, unbuffered REST payloads to completely bypass proxy buffering (e.g., Nginx, Vercel edge) common with raw streaming endpoints.
* **Database**: **SQLite** + async SQLAlchemy for session, birth data, and message history caching.
* **Frontend**: React 18 + Vite 5 + TailwindCSS 3.
* **Premium UI Overlay**: Beautiful custom frosted glass (`backdrop-filter`) layout for optimal text legibility over stardust animated backgrounds.
* **Typewriter Simulation**: An advanced typewriter hook that parses Markdown bold asterisks (`**`) into golden-highlighted tags, splits lists (`*`, `-`) into bulleted layouts, and features **organic human-paced pacing** (pausing for `180ms` at periods and newlines to simulate reading/thought).
* **Vedic Chart Wheels**: Custom SVG chart generator dynamically graphing exact degrees and ascendants.

---

## 🚀 Local Setup Guide

Follow these simple steps to run AstroAgent locally on your machine.

### Prerequisites
* **Python 3.11+**
* **Node 18+**
* **Microsoft C++ Build Tools** (Required on Windows only — to compile the `pyswisseph` Swiss Ephemeris C-bindings).

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/suyash-jaiswal2/AstroAgent.git
cd AstroAgent
```

---

### Step 2: Set Up Backend

1. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   ```
2. Activate the virtual environment:
   * **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`
   * **Windows (CMD)**: `venv\Scripts\activate.bat`
   * **Mac/Linux**: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure local environment variables:
   ```bash
   cp .env.example .env
   ```
   * Open the `.env` file and input your keys:
     * `GEMINI_API_KEY`: Obtain a free key from Google AI Studio (Highly recommended).
     * `GROQ_API_KEY`: Obtain an API key from Groq Console (Optional, used as a fallback).
5. Ingest the RAG Vector Knowledge Base:
   ```bash
   python knowledge_base/ingest.py
   ```
6. Spin up the Backend API:
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```
   * *Verify that the backend is running by visiting: [http://localhost:8000/api/health](http://localhost:8000/api/health) (Should return `{"status":"ok"}`).*

---

### Step 3: Set Up Frontend

1. Open a new terminal window, navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to: **[http://localhost:5173](http://localhost:5173)** to start exploring the stars!

---

## 🧪 Scorecard & Automated Evaluations

AstroAgent includes a comprehensive **Automated Evaluation Suite** that grades agent behavior across 30 versioned golden test cases. The evaluation suite utilizes a Gemini LLM judge to verify astrological accuracy, intent alignment, and safety conformance.

To run the evaluations:
1. Ensure your local backend is running (on `port 8000`).
2. Run the evaluation command:
   ```bash
   python eval/run_eval.py
   ```
* **Specific Categories**: You can run evaluations for single categories:
  ```bash
  python eval/run_eval.py --category chart_request_valid
  ```
* **Dry-Run**: Validate formatting and configurations:
  ```bash
  python eval/run_eval.py --dry-run
  ```

Score logs and historic scorecard details are saved in `eval/results_log.md` and detailed json files in `eval/results/`.

---

## 📂 Project Structure

```
AstroAgent/
├── backend/
│   ├── agent/
│   │   ├── graph.py          # StateGraph assembly
│   │   ├── nodes.py          # Node logic & Gemini/Groq LLM model definitions
│   │   ├── state.py          # AstroAgentState schema definitions
│   │   └── tools/            # 9 computational tool modules
│   ├── api/                  # FastAPI endpoints & CORS configurations
│   ├── db/                   # Async SQLite database and session CRUD
│   └── knowledge_base/       # 112 curated markdown texts & VectorDB ingest
├── frontend/
│   └── src/
│       ├── components/       # Glowing Orb, Observatory, Panchang, & SVG Chart widgets
│       ├── pages/            # Landing page, BirthDetails, & ChatExplorer
│       ├── hooks/            # useSSE (dynamic typewriter hook), useOrbMood
│       └── store/            # Zustand global persistent state manager
├── eval/
│   ├── golden_set.jsonl      # 30 versioned LLM safety & calculation test cases
│   ├── run_eval.py           # Auto-eval judge script
│   └── results_log.md        # Scorecard history log
└── README.md                 # Primary documentation
```