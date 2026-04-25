# Evaluation — Metrics, Dataset, and Methodology

## Quick Start

```bash
# CLI (saves markdown + JSON report to reports/)
make eval            # 10 cases
make eval-full       # all 50

# Via running API
curl -X POST "http://localhost:8000/eval/golden?limit=10" | jq
```

---

## Golden Dataset

**Location:** `evaluation/golden_cases.json`  
**Size:** 50 cases  
**Format:** Each case contains a transcript and expected triage output.

```json
{
  "call_id": "gc_001",
  "transcript": "bhai fire at CP, 3 log phase hai andar",
  "expected": {
    "incident_type": "fire",
    "severity": "CRITICAL",
    "location_node_id": "N04",
    "required_resources": ["fire_truck", "ambulance"],
    "is_duplicate": false
  }
}
```

**Dataset construction:**
- 40 unique incidents covering all 5 types (fire, medical, accident, crime, hazard)
- All 4 severity levels represented (CRITICAL/HIGH/MEDIUM/LOW)
- 10 duplicate pairs (same incident, different transcripts or languages)
- Transcripts in English, Hindi, and Hinglish (mixed code-switching)
- Noise injected: filler words, incomplete sentences, wrong word order

---

## Metrics

### Triage Metrics

| Metric | Definition |
|---|---|
| `type_accuracy` | Fraction of cases where predicted `incident_type` == expected |
| `severity_accuracy` | Fraction where predicted `severity` == expected exactly |
| `severity_within_one_accuracy` | Fraction where predicted severity is within ±1 level of expected |
| `location_accuracy` | Fraction where predicted `location_node_id` == expected |
| `resources_exact_rate` | Fraction where the *set* of required resources matches exactly |
| `avg_confidence` | Mean confidence score across all cases |

Severity order for within-one tolerance: CRITICAL > HIGH > MEDIUM > LOW (distance = 1 if adjacent).

### Deduplication Metrics

Evaluated on the 10 duplicate pairs (20 calls total):

| Metric | Definition |
|---|---|
| `precision` | True positives / (True positives + False positives) |
| `recall` | True positives / (True positives + False negatives) |
| `f1` | Harmonic mean of precision and recall |

A "true positive" is a call the system correctly identifies as a duplicate of the expected call.

---

## Implementation

### `evaluation/metrics.py`

`evaluate_triage_case(result, expected)` — computes per-case boolean correctness flags.  
`aggregate_triage(results)` — averages across all cases into `TriageMetrics`.  
`evaluate_dedup(results, cases)` — computes dedup precision/recall/F1.

### `evaluation/evaluator.py`

`run_evaluation(agent, limit)` — runs all (or `limit`) golden cases sequentially through the live `TriageAgent` instance. Returns `EvalReport` with both metric blocks and per-case detail.

Uses the **running agent instance** (injected from API startup) so embedding models and FAISS indices are already warm — no cold-start overhead per eval run. The same agent instance is used for all calls in the run, so the deduplication FAISS index accumulates across calls in time-sorted order (preserving the "5th call is a dup of 1st call" relationship).

### `evaluation/report.py`

`render_markdown(report)` — pretty-prints a metric table + per-case results table.  
`save_report(report, dir)` — writes both `.md` and `.json` files for archival.

---

## Target Thresholds

| Metric | Target |
|---|---|
| `type_accuracy` | ≥ 0.90 |
| `severity_accuracy` | ≥ 0.80 |
| `severity_within_one_accuracy` | ≥ 0.95 |
| `location_accuracy` | ≥ 0.85 |
| `resources_exact_rate` | ≥ 0.75 |
| Dedup F1 | ≥ 0.85 |

These thresholds are informed by the difficulty of the task (Hinglish, noisy transcripts, ambiguous locations) rather than arbitrary targets. The within-one severity tolerance accounts for the legitimate ambiguity between adjacent severity levels in real calls.

---

## Notes on Non-Determinism

LLM outputs are stochastic. Running the same eval twice may yield slightly different scores (typically ±2–3%). To get stable numbers for a report:

1. Use `--limit 50` (full dataset) to reduce variance
2. Consider running 3 times and averaging
3. Set `temperature=0` in the LLM config (Groq/OpenAI support this; current default is provider default)

The `per_case` field in the API response shows which cases failed, enabling targeted prompt iteration.





┌──────┬─────────────────────────────┬───────────────┐                                                                                                                                                             
  │ Node │            Place            │     Type      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N01  │ Connaught Place             │ Commercial    │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤                                                                                                                                                             
  │ N02  │ India Gate                  │ Heritage      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤                                                                                                                                                             
  │ N03  │ AIIMS Hospital              │ Hospital      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N04  │ Safdarjung Hospital         │ Hospital      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N05  │ Karol Bagh Market           │ Market        │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N06  │ Chandni Chowk               │ Market        │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N07  │ Red Fort                    │ Heritage      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N08  │ New Delhi Railway Station   │ Transport hub │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N09  │ Hazrat Nizamuddin           │ Transport hub │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N10  │ IGI Airport Terminal 3      │ Transport hub │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N11  │ Dwarka Sector 21            │ Residential   │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N12  │ Rohini Sector 7             │ Residential   │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N13  │ Saket Select Citywalk       │ Commercial    │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N14  │ Lajpat Nagar Central Market │ Market        │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N15  │ Nehru Place                 │ Commercial    │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N16  │ Hauz Khas Village           │ Commercial    │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N17  │ Lotus Temple                │ Heritage      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N18  │ Akshardham Temple           │ Heritage      │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤
  │ N19  │ Yamuna Bank Metro Station   │ Transport hub │                                                                                                                                                             
  ├──────┼─────────────────────────────┼───────────────┤    
  │ N20  │ Kashmere Gate ISBT          │ Transport hub │                                                                                                                                                             
  └──────┴─────────────────────────────┴───────────────┘
                                               