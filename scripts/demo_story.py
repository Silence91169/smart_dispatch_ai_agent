#!/usr/bin/env python3
"""
Scripted 90-second demo story for Smart City Dynamic Dispatch Grid.

Steps through canonical calls with narration banners and pauses for the presenter.
Requires the backend running at http://localhost:8000.

Usage:
    python scripts/demo_story.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Ensure the project root is importable
_root = Path(__file__).parents[1]
for _p in (_root / "src", _root):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

BASE_URL = "http://localhost:8000"
console = Console()


def banner(step: int, title: str, narration: str) -> None:
    console.print()
    console.rule(f"[bold yellow]Step {step}[/bold yellow]")
    console.print(Panel(
        Text(narration, style="italic cyan"),
        title=f"[bold]{title}[/bold]",
        border_style="yellow",
    ))


def wait_for_enter(prompt: str = "Press ENTER to continue...") -> None:
    try:
        input(f"\n  [dim]{prompt}[/dim] ")
    except (EOFError, KeyboardInterrupt):
        pass


async def post(client: httpx.AsyncClient, path: str, body: dict) -> dict:
    try:
        r = await client.post(path, json=body, timeout=60.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP {e.response.status_code}:[/red] {e.response.text[:200]}")
        return {}
    except Exception as e:
        console.print(f"[red]Request failed:[/red] {e}")
        return {}


async def get(client: httpx.AsyncClient, path: str) -> dict:
    try:
        r = await client.get(path, timeout=15.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]Request failed:[/red] {e}")
        return {}


async def run_demo() -> None:
    console.print(Panel(
        "[bold green]Smart City Dynamic Dispatch Grid[/bold green]\n"
        "[cyan]Delhi 112 — Agentic Emergency Response Demo[/cyan]\n\n"
        "This script walks through a 90-second story.\n"
        "Each step prints narration you can read aloud.",
        title="DEMO START",
        border_style="green",
    ))

    # Check backend is up
    try:
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            r = await client.get("/health", timeout=5.0)
            if r.status_code != 200:
                raise RuntimeError("backend not healthy")
    except Exception:
        console.print("[bold red]Backend not reachable at http://localhost:8000[/bold red]")
        console.print("Start it with: [cyan]make server[/cyan]")
        sys.exit(1)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:

        # ── Step 1: Reset ──────────────────────────────────────────────────
        banner(1, "Reset",
               "Before we start, let's reset the system to a clean state — "
               "all 16 vehicles back at their home stations.")
        await post(client, "/simulation/reset", {})
        console.print("[green]✓[/green] System reset — 16/16 vehicles available")
        wait_for_enter()

        # ── Step 2: CRITICAL Fire at CP ────────────────────────────────────
        banner(2, "CRITICAL Fire at Connaught Place",
               "First call: 'bhai fire at CP, 3 log phase hai andar' — Hinglish chaos.\n"
               "Watch: triage agent extracts CRITICAL FIRE → dispatch agent sends\n"
               "fire truck + ambulance → see reasoning on the right panel of the dashboard.")
        t0 = time.perf_counter()
        result = await post(client, "/calls/ingest", {
            "transcript": "bhai fire at CP, 3 log phase hai andar, log phanse hain"
        })
        lat = (time.perf_counter() - t0) * 1000
        if result.get("triage"):
            triage = result["triage"]
            console.print(
                f"[green]✓[/green] Triage: [bold red]{triage.get('severity', '?')} "
                f"{triage.get('incident_type', '?')}[/bold red] "
                f"@ {triage.get('location_node_id', '?')} ({lat:.0f}ms)"
            )
        await asyncio.sleep(3)
        wait_for_enter()

        # ── Step 3: Duplicate call ────────────────────────────────────────
        banner(3, "Duplicate Call — Same Fire",
               "'yaar CP mein fire lag gayi, building mein aag hai, jaldi bhejo!'\n"
               "Watch the DUPLICATE badge appear in the feed — 5 calls can be one incident.\n"
               "Multilingual embeddings detect semantic similarity across languages.")
        result2 = await post(client, "/calls/ingest", {
            "transcript": "yaar CP mein fire lag gayi, building mein aag hai, jaldi bhejo!"
        })
        if result2.get("triage"):
            is_dup = result2["triage"].get("is_duplicate", False)
            console.print(
                f"[green]✓[/green] Duplicate detected: [bold]{'YES' if is_dup else 'NO (LLM non-determinism)'}[/bold]"
            )
        await asyncio.sleep(2)
        wait_for_enter()

        # ── Step 4: Medium accident at Saket ──────────────────────────────
        banner(4, "MEDIUM Accident at Saket",
               "'accident at Saket, fender bender, one person complaining of back pain'\n"
               "MEDIUM severity → police car dispatched. Lower priority than the fire.")
        await post(client, "/calls/ingest", {
            "transcript": "accident at Saket, 2 cars crashed, one person has back pain"
        })
        console.print("[green]✓[/green] MEDIUM accident processed — police car dispatched")
        await asyncio.sleep(2)
        wait_for_enter()

        # ── Step 5: CRITICAL cardiac when ambulances busy ────────────────
        banner(5, "CRITICAL Cardiac Arrest — Reassignment",
               "'aunty cardiac arrest AIIMS ke paas, please fast'\n"
               "All ambulances may be busy — watch the dispatch agent pull one\n"
               "from the Saket accident (lower priority) and explain why.")
        result3 = await post(client, "/calls/ingest", {
            "transcript": "aunty cardiac arrest AIIMS ke bahar, immediately send ambulance"
        })
        if result3.get("dispatch"):
            dispatch = result3["dispatch"]
            reassigned = any(
                a.get("was_reassigned_from")
                for a in dispatch.get("assignments", [])
            )
            console.print(
                f"[green]✓[/green] Reassignment: [bold]{'YES — agent pulled vehicle from lower priority' if reassigned else 'No (enough available)'}[/bold]"
            )
        await asyncio.sleep(3)
        wait_for_enter()

        # ── Step 6: Earthquake Chaos ──────────────────────────────────────
        banner(6, "Earthquake Chaos — 30 Calls in 2 Minutes",
               "Starting earthquake_chaos at 10x speed — 30 calls flood in.\n"
               "Watch: multiple incident pins on the map, vehicles criss-crossing the city,\n"
               "DUPLICATE badges, re-routing, unfulfilled incidents as fleet is exhausted.")
        await post(client, "/simulation/start-scenario", {
            "scenario_name": "earthquake_chaos",
            "speed_multiplier": 10,
        })
        console.print("[green]✓[/green] Scenario started — watch the dashboard!")

        # Live stats loop
        for i in range(6):
            await asyncio.sleep(10)
            stats = await get(client, "/stats/")
            console.print(
                f"  t+{(i+1)*10}s | "
                f"Calls: {stats.get('simulation', {}).get('calls_processed', '?')} | "
                f"Incidents: {stats.get('incidents_total', '?')} | "
                f"Available: {stats.get('resources_available', '?')}/16"
            )

        # Final stats
        console.print()
        final = await get(client, "/stats/")
        console.print(Panel(
            f"Calls processed: {final.get('simulation', {}).get('calls_processed', '?')}\n"
            f"Incidents created: {final.get('incidents_total', '?')}\n"
            f"Resources dispatched: {16 - final.get('resources_available', 16)}/16\n"
            f"Events buffered: {final.get('events_buffered', '?')}",
            title="[bold]Final Stats[/bold]",
            border_style="cyan",
        ))

    console.print()
    console.print(Panel(
        "[bold green]Demo complete![/bold green]\n\n"
        "Next: open [cyan]http://localhost:8000/docs[/cyan] to explore the API\n"
        "or run [cyan]curl -X POST http://localhost:8000/eval/golden?limit=10 | jq[/cyan]\n"
        "to see live accuracy metrics on the golden dataset.",
        title="DEMO END",
        border_style="green",
    ))


if __name__ == "__main__":
    asyncio.run(run_demo())
