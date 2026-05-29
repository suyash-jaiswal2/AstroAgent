# AstroAgent Architecture

## System Overview
```
User Browser
│
▼
React Frontend (Vite)
│  SSE stream + REST
▼
FastAPI Backend
│
├─ LangGraph Agent
│   ├─ precheck_node       (regex safety, no LLM)
│   ├─ intent_router_node  (Haiku, 50 tokens, JSON output)
│   ├─ reasoning_node      (Haiku, full ReAct, max 8 steps)
│   ├─ tool_node           (LangGraph ToolNode — 9 tools)
│   └─ response_formatter  (disclaimer injection)
│
├─ Tool Layer
│   ├─ geocode_place        → Nominatim API (HTTP)
│   ├─ compute_birth_chart  → pyswisseph (local C lib)
│   ├─ get_daily_transits   → pyswisseph (local C lib)
│   ├─ knowledge_lookup     → ChromaDB (local persistent)
│   ├─ find_muhurta         → pyswisseph (1440 slot scan)
│   ├─ compute_compatibility → in-process computation
│   ├─ detect_yogas         → in-process computation
│   ├─ get_panchang         → pyswisseph (local C lib)
│   └─ compute_dasha_timeline → in-process computation
│
├─ SQLite (via aiosqlite)
│   ├─ sessions             (session metadata)
│   ├─ messages             (conversation history)
│   └─ cached_geocodes      (Nominatim response cache)
│
└─ ChromaDB
└─ astrology_knowledge  (112 docs, ~140 chunks, 384-dim embeddings)
```
## Data Flow — Chart Request
```
User: "What does my chart say about career?"
│
▼
precheck: no injection → pass
│
▼
intent_router: → "chart_request"
│
▼
reasoning (step 1):
→ calls geocode_place("New Delhi, India")
│
▼
tool_node: geocode → {lat: 28.61, lon: 77.21, tz: "Asia/Kolkata"}
│
▼
reasoning (step 2):
→ calls compute_birth_chart(date, time, lat, lon, tz)
│
▼
tool_node: pyswisseph → full tropical + sidereal chart
│
▼
reasoning (step 3):
→ calls knowledge_lookup("Leo sun career 10th house")
│
▼
tool_node: ChromaDB → top-3 relevant chunks
│
▼
reasoning (step 4, no tool call):
→ generates grounded response using chart data + knowledge
│
▼
response_formatter: appends disclaimer
│
▼
SSE stream → tokens → frontend → CelestialOrb animates
```
## State Transitions

The `AstroAgentState` TypedDict flows through every node. Key invariants:
- `natal_chart` is computed once and cached in both state and SQLite — never recomputed
- `step_count` is strictly bounded by `max_steps = 8` to prevent runaway loops
- `intent` is set by `intent_router` and used by `response_formatter` for disclaimer logic
- `_eval_mode` flag adds extra metadata to responses during eval runs (stripped in production)
