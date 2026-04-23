# Smart City Dynamic Dispatch Grid

An agentic AI system that ingests 112 call transcripts, triages emergencies, and dispatches civic resources (ambulances, fire trucks, police) — visualised on a live dashboard.

## Architecture Overview

```
112 transcripts
     │
     ▼
┌─────────────┐     structured data     ┌──────────────────┐
│ Triage Agent│ ──────────────────────▶ │ Dispatch Agent   │
│  (LangGraph)│  deduplication signal   │  (LangGraph)     │
└─────────────┘                         └──────────────────┘
                                                │
                                      graph-based routing
                                                │
                                         ┌──────┴──────┐
                                         │  FastAPI    │
                                         │  REST API   │
                                         └──────┬──────┘
                                                │
                                         ┌──────▼──────┐
                                         │  Dashboard  │
                                         │  (live map) │
                                         └─────────────┘
```

LLM calls are abstracted behind a common interface so Groq, Anthropic, and OpenAI are interchangeable via a single env var.

## Setup

```bash
# 1. Create a virtual environment (uv recommended)
uv venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
uv pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in at least one API key
```

## Switching LLM Providers

Change `LLM_PROVIDER` in your `.env` file:

```dotenv
LLM_PROVIDER=groq        # default — fastest for dev
# LLM_PROVIDER=anthropic
# LLM_PROVIDER=openai
```

The corresponding `*_API_KEY` and `*_MODEL` variables must also be set for the chosen provider.

## Running the Test Script

```bash
python scripts/test_llm.py
```

This health-checks every configured provider and runs both a plain completion and a structured output call.

## Running Tests

```bash
pytest
```

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project scaffolding & LLM abstraction layer | ✅ Complete |
| 2 | Triage Agent — transcript parsing & deduplication | ⬜ |
| 3 | Resource database & Dispatch Agent | ⬜ |
| 4 | Graph-based shortest-path routing | ⬜ |
| 5 | FastAPI REST server | ⬜ |
| 6 | Live dashboard (map + resource panel) | ⬜ |
| 7 | Streaming / WebSocket updates | ⬜ |
| 8 | Load testing & production hardening | ⬜ |
