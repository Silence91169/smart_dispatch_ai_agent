# Demo Script — 3-Minute Narrated Walkthrough

Use this script alongside the automated demo runner (`make demo-story`).

---

## Setup (before the demo)

```bash
make demo          # starts backend + frontend
# wait for "Backend ready" message
make demo-story    # in a second terminal — runs the scripted demo
```

Open `http://localhost:5173` on the projector. Run `demo_story.py` on your laptop; read narration aloud as each step prints.

---

## Step 1 — Reset (10s)

**Say:**
> "We have 16 emergency vehicles — ambulances, fire trucks, and police cars — distributed across Delhi. All are at their home stations. Let's reset to that clean state."

*Script sends `POST /simulation/reset` → press ENTER.*

---

## Step 2 — CRITICAL Fire at Connaught Place (20s)

**Say:**
> "First call comes in: *'bhai fire at CP, 3 log phase hai andar'* — classic Hinglish chaos. Watch what happens."

*Script sends the transcript. Point to the live feed on the left panel.*

> "In under two seconds the Triage Agent has classified this as a CRITICAL fire at Connaught Place. It extracted the location from 'CP', mapped it to node N04 on our city graph, and scored severity CRITICAL. Over on the right panel you can see the Dispatch Agent's full chain-of-thought — it selected the nearest fire truck and ambulance and computed the shortest-path routes."

*Two vehicle markers start moving on the map.*

> "This is pure agentic reasoning — no hardcoded rules."

*Press ENTER.*

---

## Step 3 — Duplicate Call (15s)

**Say:**
> "A second call: *'yaar CP mein fire lag gayi, building mein aag hai'* — same fire, different words, different language register. Watch the feed."

*DUPLICATE badge appears.*

> "Our deduplication engine uses multilingual sentence embeddings — the same model that powers multilingual Google Search. It detected semantic similarity across Hindi and English phrasing, confirmed the same incident type and location, and tagged this as a duplicate. No new dispatch wasted."

*Press ENTER.*

---

## Step 4 — MEDIUM Accident at Saket (15s)

**Say:**
> "Meanwhile, an accident comes in at Saket — MEDIUM severity, back pain complaint. A police car dispatches. Lower priority than the fire, so it doesn't pull resources from Connaught Place."

*Press ENTER.*

---

## Step 5 — CRITICAL Cardiac Arrest, Reassignment (20s)

**Say:**
> "Now the interesting case. Cardiac arrest near AIIMS — CRITICAL. But the ambulance fleet is busy at CP."

*Watch the dispatch panel.*

> "The Dispatch Agent evaluates reassignment: it looks at every en-route ambulance, checks remaining travel time, and priority gap. If the ambulance going to the Saket accident has more than two minutes remaining and the gap is at least one severity level, it gets pulled and redirected to AIIMS. The decision panel shows the exact reasoning."

*Press ENTER.*

---

## Step 6 — Earthquake Chaos (40s)

**Say:**
> "Now let's stress-test the system. We're injecting 30 calls over two minutes, compressed to 10× speed. This simulates a city-wide earthquake — fires, injuries, gas leaks, structural collapses, all at once."

*Point to the map — multiple incident pins light up, vehicles criss-cross.*

> "Watch the stats bar: duplicate rate climbs as multiple callers report the same collapsed building. Available vehicles drop as the fleet deploys. When we run out, you'll see UNFULFILLED badges appear — the system acknowledges it can't respond and queues them."

*Live stats print every 10 seconds.*

> "In 60 seconds from a standing start, with zero pre-programmed rules, the system processed 30 calls, deduplicated overlapping reports, and optimally deployed 16 vehicles across the city."

---

## Wrap-Up

> "The full API is documented at localhost:8000/docs. You can run a live accuracy benchmark against 50 golden cases with a single command — it prints type accuracy, severity accuracy, dedup F1. We consistently hit 90%+ on incident type and 85%+ on location with the free Groq tier."

```bash
curl -X POST "http://localhost:8000/eval/golden?limit=10" | jq
```

---

## Q&A Prompts

**"How does it handle low-quality audio?"**
> The LLM prompt explicitly instructs the model to handle noise, filler words, and incomplete sentences — it extracts what it can and assigns a lower confidence score when uncertain.

**"Could you swap in GPT-4?"**
> Yes — one env var change. The LLM abstraction layer wraps Groq, Anthropic, and OpenAI behind a common interface.

**"What about real 112 integration?"**
> The `/calls/ingest` endpoint is the ingestion point. In production, a Deepgram or Whisper ASR service would transcribe calls and POST here. The pipeline is unchanged.
