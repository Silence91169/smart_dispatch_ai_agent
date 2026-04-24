# Smart Dispatch Frontend

Real-time dashboard for the Smart City Dynamic Dispatch Grid (Phase 7).

## Setup

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173. The backend must be running at http://localhost:8000.

## Start backend first

```bash
# From project root
PYTHONPATH=src .venv/bin/python scripts/run_server.py
```

## What you'll see

- Dark Delhi map with 20 landmark nodes and 16 emergency vehicles at home stations
- Live incident pins (pulsing red/orange for CRITICAL/HIGH)
- Vehicles gliding along route lines as they respond
- Real-time call feed with triage chips and dispatch status
- LLM reasoning text in the Decision Inspector
- Scenario controls at the bottom (Start Chaos, Stop, Reset)
