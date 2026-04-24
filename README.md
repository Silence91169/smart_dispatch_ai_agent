# Smart City Dynamic Dispatch Grid

> **Delhi 112 reimagined** — an agentic AI system that processes Hinglish emergency call transcripts end-to-end: triage, deduplication, vehicle dispatch, and live city-map visualisation — all in real time with zero hardcoded rules.

---

## Table of Contents

- [What This Is](#what-this-is)
- [Quick Start](#quick-start)
- [How It Works — End to End](#how-it-works--end-to-end)
- [Architecture](#architecture)
  - [Pipeline Overview](#pipeline-overview)
  - [Layer 1 — API & Ingestion](#layer-1--api--ingestion)
  - [Layer 2 — Triage Agent](#layer-2--triage-agent)
  - [Layer 3 — Dispatch Agent](#layer-3--dispatch-agent)
  - [Layer 4 — Event Bus & WebSocket](#layer-4--event-bus--websocket)
  - [Layer 5 — Frontend Dashboard](#layer-5--frontend-dashboard)
- [LLM Abstraction Layer](#llm-abstraction-layer)
- [City Graph — Delhi in 20 Nodes](#city-graph--delhi-in-20-nodes)
- [Fleet — 16 Vehicles](#fleet--16-vehicles)
- [Data Layer](#data-layer)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Evaluation & Accuracy](#evaluation--accuracy)
- [Testing Strategy](#testing-strategy)
- [Common Commands](#common-commands)
- [Switching LLM Providers](#switching-llm-providers)
- [Demo Walkthrough](#demo-walkthrough)

---

## What This Is

Real emergency dispatch centers receive calls in chaotic conditions — incomplete sentences, mixed Hindi-English (Hinglish), background noise, duplicate callers reporting the same incident. Human operators must quickly classify the emergency, find the right resources, and route them optimally.

This project automates that pipeline using AI agents:

1. A raw call transcript comes in (e.g. *"bhai fire at CP, 3 log phase hai andar"*)
2. The **Triage Agent** extracts incident type, severity, and location using an LLM — handling noisy Hinglish naturally
3. The **Deduplicator** checks if this is the 5th caller reporting the same fire — if so, it's suppressed
4. The **Dispatch Agent** finds the nearest available vehicle, computes the shortest path on a city graph, and handles reassignment if a higher-priority emergency arrives
5. Every decision streams live to a **React dashboard** with a Leaflet map showing vehicles moving in real time

No rules were hardcoded. Every classification, severity rating, and routing decision is made by the AI pipeline.

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd smart-dispatch
cp .env.example .env        # add your GROQ_API_KEY (or ANTHROPIC / OPENAI)
uv sync
cd frontend && npm install && cd ..

# 2. Start everything
make demo                   # starts backend on :8000 + frontend on :5173

# 3. Open the dashboard
open http://localhost:5173
```

The API docs are available at `http://localhost:8000/docs`.

---

## How It Works — End to End

Here is the full journey of a single emergency call through the system:

```
Caller dials 112
       │
       ▼
POST /calls/ingest { "transcript": "bhai fire at CP, 3 log phase hai andar" }
       │
       ├─► EventBus publishes CALL_RECEIVED  ──► WebSocket fans out to dashboard
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│                    TRIAGE AGENT                          │
│                                                          │
│  Step 1 — Preprocess                                     │
│    Normalize whitespace, strip filler words              │
│                                                          │
│  Step 2 — LLM Structured Extraction                      │
│    Single prompt → JSON: incident_type, severity,        │
│    location_text, required_resources, confidence,        │
│    summary, reasoning                                    │
│                                                          │
│  Step 3 — Location Resolution (3-tier)                   │
│    Tier 1: exact name match (confidence 1.0)             │
│    Tier 2: alias/abbreviation match — "CP" → N01         │
│    Tier 3: multilingual semantic embedding similarity    │
│                                                          │
│  Step 4 — Deduplication (4-criteria gate)                │
│    ① same incident type                                  │
│    ② within 15-minute time window                        │
│    ③ location same node or adjacent in graph             │
│    ④ embedding cosine similarity ≥ 0.75                  │
│    All 4 must pass → duplicate suppressed                │
└──────────────────────┬───────────────────────────────────┘
                       │ TriageResult (structured)
                       ├─► EventBus publishes TRIAGE_COMPLETED
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│                   DISPATCH AGENT                         │
│                                                          │
│  Step 1 — Enqueue                                        │
│    Push TriageResult into IncidentPriorityQueue          │
│    (min-heap: CRITICAL=0, HIGH=1, MEDIUM=2, LOW=3)       │
│                                                          │
│  Step 2 — Vehicle Selection                              │
│    Query ResourceDB for AVAILABLE vehicles of each type  │
│    Run Dijkstra on city graph → shortest path + ETA      │
│    Pick nearest available vehicle                        │
│                                                          │
│  Step 3 — Reassignment Check (if no vehicle available)   │
│    Find all EN_ROUTE candidates                          │
│    For each: check severity gap ≥ 1 level,               │
│    check remaining ETA ≥ 120s, check not ON_SCENE        │
│    If all pass → pull vehicle, redirect to new incident  │
│                                                          │
│  Step 4 — LLM Reasoning                                  │
│    Generate human-readable explanation of the decision   │
│    shown in the Decision Inspector panel                 │
│                                                          │
│  Step 5 — Commit                                         │
│    Update ResourceDB: AVAILABLE → DISPATCHED             │
│    Write DispatchLog                                     │
└──────────────────────┬───────────────────────────────────┘
                       │ DispatchDecision
                       ├─► EventBus publishes RESOURCE_DISPATCHED
                       │
                       ▼
              WebSocket fan-out to all dashboard clients
              Vehicle marker animates along path on the map
```

---

## Architecture

### Pipeline Overview

```
112 call transcript (Hinglish / English / Hindi)
         │
         ▼
┌─────────────────────┐   TriageResult (JSON)   ┌──────────────────────┐
│   Triage Agent      │ ──────────────────────► │   Dispatch Agent     │
│                     │                          │                      │
│  • LLM extraction   │   dedup signal           │  • priority queue    │
│  • 3-tier location  │ ──────────────────────► │  • Dijkstra routing  │
│  • FAISS dedup      │                          │  • reassignment      │
│  • severity rating  │                          │  • unfulfilled track │
└─────────────────────┘                          └──────────┬───────────┘
                                                            │
              ┌─────────────────────────────────────────────┘
              │
              ▼
        EventBus (in-process pub/sub)
              │
              ▼
   FastAPI REST + WebSocket layer
              │
              ▼
   React Dashboard (Leaflet map · Zustand · Tailwind)
```

---

### Layer 1 — API & Ingestion

**Location:** `src/smart_dispatch/api/`

The FastAPI application exposes the following route groups:

| Route prefix | Purpose |
|---|---|
| `POST /calls/ingest` | Main ingestion — accepts a transcript, runs full triage + dispatch pipeline |
| `GET /incidents/` | List all incidents with status, severity, location |
| `GET /resources/` | Current fleet status (available, dispatched, on_scene) |
| `GET /decisions/` | Dispatch decision history with LLM reasoning |
| `POST /simulation/reset` | Reset all vehicles to home stations |
| `POST /simulation/start-scenario` | Start a bulk scenario (e.g. earthquake_chaos) |
| `GET /stats/` | System-wide stats (call count, duplicate rate, fleet availability) |
| `GET /graph/` | City graph topology for the frontend map |
| `POST /eval/golden` | Run accuracy benchmark against the golden dataset |
| `WS /ws` | WebSocket endpoint — streams all events to connected clients |

**Concurrency:** The API is fully async (FastAPI + uvicorn + aiosqlite). A single `asyncio.Lock` in `ResourceDB.dispatch_resource` prevents two coroutines from double-dispatching the same vehicle under concurrent load.

---

### Layer 2 — Triage Agent

**Location:** `src/smart_dispatch/agents/triage/`

The TriageAgent is the AI brain that converts a raw noisy transcript into a structured incident record.

#### Step 1 — Preprocessing (`preprocessor.py`)

Cleans the transcript before sending to the LLM: normalizes whitespace, collapses repeated characters, handles common voice-to-text artifacts. The LLM prompt itself instructs the model to tolerate noise, filler words, and incomplete sentences.

#### Step 2 — LLM Structured Extraction (`agent.py`, `prompts.py`, `schemas.py`)

A single LLM call returns a JSON object constrained to the `LLMTriageExtraction` Pydantic schema:

```json
{
  "incident_type": "fire",
  "severity": "CRITICAL",
  "location_text": "CP",
  "location_landmark": "Connaught Place",
  "required_resources": ["fire_truck", "ambulance"],
  "summary": "Fire at Connaught Place, people trapped",
  "reasoning": "Caller reported active fire with casualties...",
  "confidence": 0.95
}
```

The system prompt includes the full 20-node city graph so the LLM can map informal location references (e.g. "CP", "rajiv chowk") to their canonical node names. Severity levels are defined (CRITICAL / HIGH / MEDIUM / LOW) with examples so the model understands the scale.

**Supported incident types:** `fire`, `medical`, `accident`, `crime`, `hazard`

#### Step 3 — Location Resolution (`location_resolver.py`)

Three-tier resolution with fallback confidence:

| Tier | Method | Confidence |
|---|---|---|
| 1 | Exact name match against 20 node labels | 1.0 |
| 2 | Alias / abbreviation match (e.g. "CP" → Connaught Place, "AIIMS" → AIIMS Hospital) | 0.9 |
| 3 | Semantic embedding similarity using `multilingual-e5-small` (cosine ≥ 0.6) | proportional to score |

If all three tiers fail, the location is marked unresolved and the incident is logged but not dispatched.

#### Step 4 — Deduplication (`deduplicator.py`)

The `IncidentDeduplicator` uses FAISS (`IndexFlatIP` — inner product / cosine similarity) to detect when multiple callers are reporting the same incident.

**All four criteria must pass to call something a duplicate:**

1. **Same incident type** — a fire and a medical emergency at the same location are different incidents
2. **Within 15-minute time window** — old records are outside scope
3. **Location compatible** — same graph node OR adjacent nodes in the city graph (handles callers giving slightly different nearby landmarks)
4. **Embedding cosine similarity ≥ 0.75** — the semantic content of the calls must be similar

The dedup text is constructed as: `"fire at Connaught Place. People trapped, flames visible"` — combining incident type, location, and summary into one embedding.

When a duplicate is detected, `is_duplicate=True` is set on the `TriageResult`, the call is counted against the original incident, and no new dispatch is triggered. The dashboard shows a `DUPLICATE` badge.

---

### Layer 3 — Dispatch Agent

**Location:** `src/smart_dispatch/agents/dispatch/`

The DispatchAgent manages the priority queue, finds vehicles, handles reassignment, and generates reasoning.

#### Priority Queue (`priority_queue.py`)

`IncidentPriorityQueue` is a min-heap (`heapq`) with lazy invalidation — when an incident is removed or superseded, its old entry is marked invalid rather than removed from the heap (O(1) invalidation vs O(n) removal).

**Priority ordering:**
```
CRITICAL = 0  (highest priority — pops first)
HIGH     = 1
MEDIUM   = 2
LOW      = 3  (lowest priority)
```

When two incidents share the same severity, they are resolved FIFO by `triaged_at` timestamp.

#### Vehicle Router (`router.py`)

`VehicleRouter` runs **Dijkstra's shortest path** algorithm on the 20-node NetworkX `DiGraph` representing Delhi. Edge weights are travel times in seconds.

- `find_best_available()` — searches only `AVAILABLE` vehicles, returns the one with the minimum travel time to the incident node
- `find_all_candidates(include_busy=True)` — returns all vehicles of a type including EN_ROUTE ones, used when no available vehicle exists and reassignment is needed

#### Reassignment / Rerouter (`rerouter.py`)

When no available vehicle can be found, the `Rerouter` evaluates every in-flight vehicle of the needed type.

**Three rules — all must pass to trigger reassignment:**

1. Vehicle must NOT be `ON_SCENE` (it has already arrived — don't pull it back)
2. Severity gap must be ≥ 1 level (a CRITICAL incident can pull a MEDIUM vehicle; a HIGH cannot pull another HIGH)
3. Remaining ETA to current destination must be ≥ 120 seconds (if the vehicle is 1 minute away, let it complete)

If reassignment happens, the bumped incident is re-queued so it can pick up a different vehicle when one becomes available.

#### LLM Reasoning (`reasoning.py`)

After every dispatch decision, the `DispatchReasoner` calls the LLM to generate a human-readable explanation shown in the Decision Inspector panel on the dashboard:

> *"Dispatched DELTA-FIRE-01 from Connaught Place (N01) to Saket (N13) via shortest path — estimated 8 minutes. No reassignment needed; vehicle was available. CRITICAL severity fire with confirmed casualties."*

A deterministic fallback is always computed in case the LLM call fails.

#### Unfulfillable Incidents

If no vehicle can be assigned even after exhausting reassignment candidates, the incident is marked `UNFULFILLABLE`, an `UNFULFILLED_INCIDENT` event is published, and the dashboard shows an `UNFULFILLED` badge. The incident is automatically re-queued after 10 seconds to retry when a vehicle returns.

---

### Layer 4 — Event Bus & WebSocket

**Location:** `src/smart_dispatch/orchestration/event_bus.py`, `src/smart_dispatch/api/websocket/`

#### EventBus

An in-process async pub/sub message bus. All agents publish structured `Event` objects with a type, timestamp, and payload. The bus maintains a rolling history of 500 events for late-joining WebSocket clients.

**Event types:**

| Event | When published |
|---|---|
| `CALL_RECEIVED` | Immediately on POST /calls/ingest |
| `TRIAGE_STARTED` | When TriageAgent begins processing |
| `TRIAGE_COMPLETED` | When TriageResult is ready |
| `DUPLICATE_DETECTED` | When a call is flagged as a duplicate |
| `INCIDENT_CREATED` | When a new unique incident is registered |
| `RESOURCE_DISPATCHED` | When a vehicle is assigned and starts moving |
| `RESOURCE_REASSIGNED` | When a vehicle is pulled from one incident to another |
| `UNFULFILLED_INCIDENT` | When no vehicle can be found |
| `SIMULATION_PROGRESS` | During bulk scenario playback |
| `SYSTEM_ERROR` | On any pipeline failure |

#### WebSocket Fan-out

The `ConnectionManager` subscribes its `_broadcast` method to the EventBus. When an event is published, it is immediately sent to all connected WebSocket clients as JSON. 

React StrictMode safety: the manager tracks a `_subscribed` flag and only unsubscribes when the last client disconnects, preventing StrictMode's double-mount pattern from removing the only event subscriber.

---

### Layer 5 — Frontend Dashboard

**Location:** `frontend/src/`

A React 18 + Vite single-page app. All state is managed in a single Zustand store (`useSystemStore`). WebSocket events are handled by `handleWsEvent()` in `eventHandlers.js`, which updates the relevant slice of store state on each event.

#### Components

| Component | Purpose |
|---|---|
| `CityMap` (Leaflet) | Interactive map of Delhi with custom SVG markers |
| `VehicleMarker` | Shows each vehicle's real-time position; animates along the route path every 500ms |
| `IncidentMarker` | Pins for each active incident, color-coded by severity |
| `RouteLine` | Draws the computed Dijkstra path on the map when a vehicle is dispatched |
| `IncidentFeed` | Most-recent-first bounded list (60 items); cards progress through `triage_pending → dispatched` or `duplicate` / `error` stages |
| `DecisionInspector` | Shows the LLM's full chain-of-thought reasoning for the selected dispatch decision |
| `ResourcePanel` | Fleet overview — all 16 vehicles with their current status |
| `StatsBar` | Live counters: total calls, incidents, duplicate rate, available vehicles |
| `ScenarioControls` | Buttons to reset state or trigger bulk scenarios |
| `ManualCallInput` | Text box to submit a custom transcript directly from the dashboard |

---

## LLM Abstraction Layer

**Location:** `src/smart_dispatch/core/llm/`

All agent code receives an `LLMProvider` interface — it has no knowledge of which underlying model is used.

```
LLMProvider (abstract base)
├── GroqProvider      — Llama 3.3 70B via Groq API (default, fastest/free tier)
├── AnthropicProvider — Claude Sonnet via Anthropic API
└── OpenAIProvider    — GPT-4o-mini via OpenAI API
```

**Two method signatures all providers implement:**

- `completion(messages, **kwargs) → str` — plain text response
- `structured_output(prompt, schema, **kwargs) → PydanticModel` — JSON constrained to a Pydantic schema, with automatic retry on parse failure

**Switching providers** requires changing one environment variable — no code changes:

```env
LLM_PROVIDER=groq        # groq | anthropic | openai
```

**Testing:** A `MockLLMProvider` in `tests/mocks/mock_llm.py` returns deterministic structured responses without any network calls, enabling the full unit test suite to run in under 5 seconds with no API key.

---

## City Graph — Delhi in 20 Nodes

The city is modelled as a directed weighted graph (`NetworkX.DiGraph`). Each node is a real Delhi landmark. Edges represent road connections with travel-time weights in seconds.

| Node | Landmark | Type |
|---|---|---|
| N01 | Connaught Place | Commercial |
| N02 | India Gate | Heritage |
| N03 | AIIMS Hospital | Hospital |
| N04 | Safdarjung Hospital | Hospital |
| N05 | Karol Bagh Market | Market |
| N06 | Chandni Chowk | Market |
| N07 | Red Fort | Heritage |
| N08 | New Delhi Railway Station | Transport Hub |
| N09 | Hazrat Nizamuddin | Transport Hub |
| N10 | IGI Airport Terminal 3 | Transport Hub |
| N11 | Dwarka Sector 21 | Residential |
| N12 | Rohini Sector 7 | Residential |
| N13 | Saket Select Citywalk | Commercial |
| N14 | Lajpat Nagar Central Market | Market |
| N15 | Nehru Place | Commercial |
| N16 | Hauz Khas Village | Commercial |
| N17 | Lotus Temple | Heritage |
| N18 | Akshardham Temple | Heritage |
| N19 | Yamuna Bank Metro Station | Transport Hub |
| N20 | Kashmere Gate ISBT | Transport Hub |

The graph is loaded from a JSON fixture at startup and cached in memory. The DispatchAgent's `VehicleRouter` runs Dijkstra on this graph to compute shortest paths and travel-time ETAs for every dispatch decision.

The Triage Agent's LLM prompt includes this full node list so the model can map informal references (e.g. "CP", "rajiv chowk", "lal qila") to the correct node ID.

---

## Fleet — 16 Vehicles

| Vehicle | Count | Home Stations |
|---|---|---|
| Ambulance | 6 | AIIMS (×2), Safdarjung Hospital (×2), Connaught Place (×1), Akshardham (×1) |
| Fire Truck | 4 | Connaught Place, Chandni Chowk, Saket, Rohini |
| Police Car | 4 | Connaught Place, Karol Bagh, Lajpat Nagar, Dwarka |
| Hazmat Unit | 2 | Karol Bagh, Akshardham |

Each incident type requires specific resource types:
- **Fire** → fire truck + ambulance
- **Medical** → ambulance
- **Accident** → police car + ambulance
- **Crime** → police car
- **Hazard** → hazmat unit + fire truck

---

## Data Layer

**Location:** `src/smart_dispatch/data/`

### ResourceDB (`resource_db.py`)

SQLAlchemy 2.0 async ORM backed by SQLite (via `aiosqlite`). Three tables:

- **`resources`** — the 16-vehicle fleet with current status, position node, ETA, and dispatch count
- **`incidents`** — every unique incident created from a triaged call
- **`dispatch_logs`** — immutable audit log of every vehicle assignment

**Concurrency safety:** `dispatch_resource()` is guarded by `asyncio.Lock()` — only one coroutine can transition a resource from `AVAILABLE → DISPATCHED` at a time, preventing double-dispatch under concurrent load.

**Resource statuses:** `AVAILABLE → DISPATCHED → EN_ROUTE → ON_SCENE → RETURNING → AVAILABLE`

### Seeder (`resource_seeder.py`)

Seeds the database with the 16-vehicle fleet at startup. Idempotent — safe to run multiple times. `make reset-db` wipes and reseeds.

### Golden Dataset (`golden_dataset.py`)

50 pre-labelled test cases used by the evaluation system. Each case contains a transcript and the expected triage output.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM (default) | Groq — Llama 3.3 70B | Free tier, very fast, strong multilingual ability |
| LLM (alternatives) | Anthropic Claude Sonnet, OpenAI GPT-4o-mini | Swappable via env var |
| API framework | FastAPI + uvicorn | Async-native, auto OpenAPI docs |
| Database | SQLite via SQLAlchemy async + aiosqlite | Zero setup, sufficient for single-process |
| Embeddings | `sentence-transformers` — `multilingual-e5-small` | Supports Hindi/English/Hinglish in one model |
| Vector search | FAISS `IndexFlatIP` | Fast cosine similarity search for deduplication |
| City graph | NetworkX `DiGraph` + Dijkstra | Clean shortest-path API |
| Frontend | React 18 + Vite | Fast HMR dev experience |
| Map | Leaflet + react-leaflet | Lightweight, works offline |
| State management | Zustand | Minimal boilerplate for a live event-driven store |
| Styling | Tailwind CSS | Utility-first, rapid dashboard layout |
| Testing | pytest-asyncio + MockLLMProvider | Full suite runs with no API key |
| Package manager (Python) | uv | Fast dependency resolution |
| Package manager (JS) | npm | Standard |

---

## Project Structure

```
smart-dispatch/
├── src/smart_dispatch/
│   ├── agents/
│   │   ├── base.py                  # BaseAgent — shared lifecycle + logging
│   │   ├── triage/
│   │   │   ├── agent.py             # TriageAgent — main entrypoint
│   │   │   ├── preprocessor.py      # transcript cleaning
│   │   │   ├── location_resolver.py # 3-tier location resolution
│   │   │   ├── deduplicator.py      # FAISS-based dedup
│   │   │   ├── prompts.py           # versioned LLM system prompts
│   │   │   └── schemas.py           # TriageResult, LLMTriageExtraction Pydantic models
│   │   └── dispatch/
│   │       ├── agent.py             # DispatchAgent — main entrypoint
│   │       ├── priority_queue.py    # IncidentPriorityQueue (min-heap, lazy invalidation)
│   │       ├── router.py            # VehicleRouter — Dijkstra on city graph
│   │       ├── rerouter.py          # Rerouter — reassignment decision logic
│   │       ├── reasoning.py         # DispatchReasoner — LLM explanation generation
│   │       └── schemas.py           # DispatchDecision, ResourceAssignment Pydantic models
│   ├── api/
│   │   ├── main.py                  # FastAPI app factory, startup/shutdown hooks
│   │   ├── routes/
│   │   │   ├── calls.py             # POST /calls/ingest
│   │   │   ├── incidents.py         # GET /incidents/
│   │   │   ├── resources.py         # GET /resources/
│   │   │   ├── decisions.py         # GET /decisions/
│   │   │   ├── simulation.py        # POST /simulation/reset, /start-scenario
│   │   │   ├── stats.py             # GET /stats/
│   │   │   ├── graph.py             # GET /graph/
│   │   │   └── eval.py              # POST /eval/golden
│   │   ├── websocket/
│   │   │   ├── manager.py           # ConnectionManager — fan-out to all clients
│   │   │   └── routes.py            # WS /ws endpoint
│   │   └── simulation.py            # Bulk scenario playback engine
│   ├── core/
│   │   ├── llm/
│   │   │   ├── base.py              # LLMProvider abstract base
│   │   │   ├── factory.py           # get_default_provider() — reads LLM_PROVIDER env var
│   │   │   ├── groq_provider.py
│   │   │   ├── anthropic_provider.py
│   │   │   ├── openai_provider.py
│   │   │   └── schemas.py
│   │   └── embeddings/
│   │       ├── base.py              # EmbeddingProvider abstract base
│   │       └── sentence_transformer_provider.py  # multilingual-e5-small
│   ├── data/
│   │   ├── resource_db.py           # SQLAlchemy ORM — resources, incidents, dispatch_logs
│   │   ├── resource_seeder.py       # seeds the 16-vehicle fleet
│   │   ├── city_graph.py            # loads + caches the NetworkX DiGraph
│   │   ├── city_fixtures.py         # 20 Delhi node definitions with aliases
│   │   ├── golden_dataset.py        # loads the 50-case eval dataset
│   │   ├── call_generator.py        # mock call generation for simulations
│   │   └── schemas.py               # shared data models (MockCall, IncidentType, etc.)
│   ├── orchestration/
│   │   ├── event_bus.py             # async pub/sub EventBus
│   │   ├── graph.py                 # LangGraph orchestration graph
│   │   └── state.py                 # pipeline state definitions
│   └── config.py                    # Settings loaded from .env
├── evaluation/
│   ├── evaluator.py                 # run_evaluation() — runs golden cases through TriageAgent
│   ├── metrics.py                   # per-case scoring + aggregate computation
│   ├── report.py                    # markdown + JSON report generation
│   └── run_eval.py                  # CLI entrypoint
├── tests/
│   ├── conftest.py                  # shared fixtures: city_graph, fresh_db, mock_llm
│   ├── mocks/mock_llm.py            # MockLLMProvider — deterministic, no API calls
│   ├── fixtures/
│   │   ├── golden_transcripts.json
│   │   └── incident_scenarios.json
│   ├── unit/
│   │   ├── test_priority_queue.py   # heap ordering, lazy invalidation, FIFO tiebreak
│   │   ├── test_deduplicator.py     # embedding dedup — same/different type, time window
│   │   ├── test_location_resolver.py
│   │   ├── test_city_graph.py
│   │   ├── test_rerouter.py         # reassignment rules
│   │   ├── test_resource_db.py      # AVAILABLE→DISPATCHED, concurrency lock
│   │   └── test_vehicle_router.py
│   └── integration/
│       ├── test_dispatch_pipeline.py  # Hinglish call → vehicles dispatched (real LLM)
│       ├── test_triage_pipeline.py
│       └── test_api_endpoints.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── store/
│       │   ├── useSystemStore.js    # Zustand store — single source of truth
│       │   └── eventHandlers.js     # WS event → store update mapping
│       ├── components/
│       │   ├── map/                 # CityMap, VehicleMarker, IncidentMarker, RouteLine
│       │   ├── incidents/           # IncidentFeed, IncidentCard, SeverityBadge
│       │   ├── decisions/           # DecisionInspector, ReasoningBubble
│       │   ├── resources/           # ResourcePanel, ResourceCard
│       │   ├── controls/            # ScenarioControls, ManualCallInput
│       │   ├── stats/               # StatsBar
│       │   └── layout/              # TopBar, Dashboard, StatusDot
│       ├── api/
│       │   ├── client.js            # REST API client
│       │   └── websocket.js         # WebSocket connection with reconnect logic
│       └── hooks/
│           ├── useLiveConnection.js # manages WS lifecycle
│           └── useTimeAgo.js        # relative timestamps
├── scripts/
│   ├── demo_story.py       # 6-step scripted demo runner with narration banners
│   ├── simulate_scenario.py # bulk chaos scenario runner
│   ├── test_triage.py      # interactive REPL for testing triage on custom text
│   ├── test_dispatch.py    # end-to-end single-call test with rich output
│   ├── benchmark_dedup.py  # dedup precision/recall against golden dataset
│   ├── inspect_dispatches.py # dispatch history and vehicle utilization
│   ├── resource_status.py  # current fleet status table
│   ├── visualize_graph.py  # print city graph nodes, edges, and run pathfinding
│   ├── generate_sample_calls.py # dump mock calls as JSON
│   ├── stream_demo.py      # live streaming mock calls
│   ├── smoke_test_api.py   # quick HTTP smoke test
│   ├── run_server.py       # start uvicorn
│   ├── init_db.py          # init schema + seed fleet
│   └── quick_start.sh      # one-command full setup
├── docs/
│   ├── DEMO_SCRIPT.md      # word-for-word narration guide for the demo
│   └── EVALUATION.md       # evaluation methodology, metrics definitions, thresholds
├── Makefile
├── pyproject.toml
└── .env.example
```

---

## Evaluation & Accuracy

The system ships with a 50-case golden dataset (`evaluation/`) to measure real accuracy against labelled examples.

### Dataset Composition

- 40 unique incidents across all 5 types (fire, medical, accident, crime, hazard)
- All 4 severity levels represented (CRITICAL / HIGH / MEDIUM / LOW)
- 10 duplicate pairs — same incident described with different words or language registers
- Transcripts in English, Hindi, and Hinglish with noise (filler words, wrong word order, incomplete sentences)

### Metrics

| Metric | Definition | Target |
|---|---|---|
| `type_accuracy` | Predicted incident type == expected | ≥ 90% |
| `severity_accuracy` | Predicted severity == expected (exact) | ≥ 80% |
| `severity_within_one` | Predicted severity within ±1 level | ≥ 95% |
| `location_accuracy` | Predicted node ID == expected | ≥ 85% |
| `resources_exact_rate` | Predicted resource set == expected set | ≥ 75% |
| `dedup_f1` | Harmonic mean of dedup precision + recall | ≥ 0.85 |

### Running the Benchmark

```bash
make eval           # 10 cases (quick)
make eval-full      # all 50 cases
# or via API:
curl -X POST "http://localhost:8000/eval/golden?limit=10" | jq
```

Reports are saved to `reports/` as both Markdown and JSON.

**Note on non-determinism:** LLM outputs are stochastic. Running the same eval twice may yield ±2–3% variance. For stable numbers, run with `--limit 50` and consider averaging 3 runs. Set `temperature=0` in the LLM config to reduce variance.

---

## Testing Strategy

| Layer | What is tested | LLM | Speed |
|---|---|---|---|
| Unit — priority queue, router, DB | Data structures, routing math, DB transitions | MockLLMProvider (no API) | < 5s |
| Unit — embeddings, dedup | Real `sentence-transformers` model, dedup gate logic | None (embeddings only) | ~30s |
| Integration — pipeline | Full triage + dispatch with real LLM calls | Real (Groq) | ~60s |
| Evaluation — golden dataset | 50-case accuracy benchmark | Real (Groq) | ~90s |

```bash
make test                # unit tests only — no API key needed
make test-slow           # unit tests including embedding model tests
make test-integration    # real LLM integration tests — needs GROQ_API_KEY
make test-all            # everything
```

Tests are organized so you can run the full fast suite with zero external dependencies during development, and only run integration tests before committing or for CI.

---

## Common Commands

```bash
make server           # backend only (localhost:8000)
make frontend         # frontend only (localhost:5173)
make demo             # both together

make test             # fast unit tests (no API key needed)
make test-slow        # unit tests + embedding model
make test-integration # real LLM integration tests

make eval             # accuracy benchmark — 10 cases
make eval-full        # accuracy benchmark — all 50

make demo-story       # run scripted 6-step narrated demo

make reset-db         # wipe SQLite and reseed fleet
make lint             # ruff linter + autofix
make clean            # remove __pycache__, *.pyc, reports/, *.db
```

---

## Switching LLM Providers

Edit `.env`:

```env
# Default — Groq (free tier, fastest)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

No code changes needed. The `LLMProvider` abstraction layer handles all provider-specific API differences internally.

---

## Demo Walkthrough

The scripted demo (`make demo-story`) steps through 6 scenarios in ~90 seconds:

| Step | Scenario | What to watch |
|---|---|---|
| 1 | **Reset** | All 16 vehicles return to home stations |
| 2 | **CRITICAL Fire at Connaught Place** | Hinglish call → CRITICAL classification → fire truck + ambulance dispatched → vehicles animate on map |
| 3 | **Duplicate call** | Same fire, different words/language → DUPLICATE badge → no second dispatch |
| 4 | **MEDIUM Accident at Saket** | Lower priority → police car dispatched, fire resources not touched |
| 5 | **CRITICAL Cardiac Arrest — reassignment** | All ambulances busy → Dispatch Agent evaluates reassignment → pulls ambulance from Saket → Decision Inspector shows reasoning |
| 6 | **Earthquake Chaos** | 30 calls injected at 10× speed → duplicate rate climbs → fleet depletes → UNFULFILLED badges appear |

Run it:

```bash
make demo             # start backend + frontend first
make demo-story       # in a second terminal
```

Open `http://localhost:5173` on screen before running `demo-story`.
