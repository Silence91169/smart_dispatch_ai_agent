"""Full chaos simulation: triage → dispatch → live dashboard → final summary.

Usage:
  python scripts/simulate_scenario.py --scenario earthquake_chaos
  python scripts/simulate_scenario.py --scenario earthquake_chaos --speed 50
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smart_dispatch.agents.dispatch import DispatchAgent, DispatchDecision, DispatchStatus
from smart_dispatch.agents.triage import TriageAgent, TriageResult
from smart_dispatch.data.call_stream import CallStream
from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus
from smart_dispatch.data.resource_seeder import seed_fleet
from smart_dispatch.data.schemas import MockCall, Severity

console = Console()

# Pre-written Hinglish transcripts for the earthquake chaos scenario
EARTHQUAKE_CHAOS_TRANSCRIPTS = [
    "HELP! Saket mein aag lagi hai, building gir gayi!! 3-4 log phase hain andar, please jaldi aao!!!",
    "Yaar CP mein dukaan mein aag hai, gas leaking ho raha hai please fire brigade bhejo jaldi",
    "AIIMS ke paas ek bhai gira hai building se, seriously injured hai, ambulance chahiye jaldi!",
    "Dilli Haat ke paas building mein aag lagi hai, bohot smoke hai, log chilla rahe hain!",
    "Karol Bagh mein ek aadmi behosh ho gaya, earthquake ke baad, please help ambulance",
    "India Gate ke paas bahut sare log injured hain, earthquake tha abhi, ambulance bhejo fast",
    "Lajpat Nagar mein ek complex mein fire hai, cylinder phata, 2 log jal gaye seriously",
    "CP ke paas ek car accident hua, 2-3 log phanse hain andar, police aur ambulance chahiye",
    "Hauz Khas mein ek lady ka fracture ho gaya hai, move nahi kar pa rahi, jaldi aao",
    "Bhai saket mein aag hai building mein!! please help!! Fire aur ambulance dono chahiye",
    "Okhla industrial area mein chemical factory mein kuch leak ho gaya, bohot smell aa raha hai",
    "Yaar CP mein gas leak aur fire hai, dukaan jalti hai, please jaldi aao fire truck",
    "Karol Bagh mein bhai ek aadmi gira hua hai, hosh nahi hai, please ambulance jaldi",
    "Nehru Place ke paas building ka hissa gira hai, logon ke upar aa gaya, rescue chahiye",
    "Bhai Connaught Place ke paas gas pipe phata hua hai, bohot bada explosion ho sakta hai",
]

_SEV_COLOUR = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "bold yellow",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "dim",
}

_STATUS_COLOUR = {
    DispatchStatus.DISPATCHED: "green",
    DispatchStatus.PARTIALLY_DISPATCHED: "yellow",
    DispatchStatus.UNFULFILLABLE: "red",
}


def _make_call(text: str, offset_sec: int) -> MockCall:
    return MockCall(
        transcript=text,
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=offset_sec),
    )


def _build_live_panel(
    call_count: int,
    recent_triages: list[TriageResult],
    recent_decisions: list[DispatchDecision],
    fleet_counts: dict[str, int],
) -> Panel:
    # Fleet status bar
    available = fleet_counts.get("available", 0)
    dispatched = fleet_counts.get("dispatched", 0) + fleet_counts.get("en_route", 0)
    fleet_line = (
        f"[green]available={available}[/green]  "
        f"[yellow]dispatched/en_route={dispatched}[/yellow]  "
        f"[dim]other={sum(fleet_counts.values()) - available - dispatched}[/dim]"
    )

    # Recent triages
    triage_lines = []
    for t in recent_triages[-3:]:
        sev_c = _SEV_COLOUR[t.severity]
        dup_tag = " [yellow](DUP)[/yellow]" if t.is_duplicate else ""
        triage_lines.append(
            f"  [{sev_c}]{t.severity.value}[/{sev_c}] {t.incident_type.value} "
            f"@ {t.location_node_id or '?'}{dup_tag}  {t.call_id}"
        )

    # Recent decisions
    dec_lines = []
    for d in recent_decisions[-3:]:
        sc = _STATUS_COLOUR.get(d.status, "dim")
        vehicles = ", ".join(a.call_sign for a in d.assignments) or "none"
        dec_lines.append(
            f"  [{sc}]{d.status.value}[/{sc}] {d.incident_id}: {vehicles}"
        )

    body = (
        f"[bold]Calls processed:[/bold] {call_count}\n"
        f"[bold]Fleet:[/bold] {fleet_line}\n\n"
        f"[bold]Recent Triages:[/bold]\n"
        + ("\n".join(triage_lines) or "  (none)")
        + "\n\n"
        f"[bold]Recent Dispatches:[/bold]\n"
        + ("\n".join(dec_lines) or "  (none)")
    )
    return Panel(body, title="[bold cyan]Live Dispatch Dashboard[/bold cyan]", border_style="cyan")


async def get_fleet_counts(db: ResourceDB) -> dict[str, int]:
    all_res = await db.list_resources()
    counts: dict[str, int] = {}
    for r in all_res:
        counts[r.status.value] = counts.get(r.status.value, 0) + 1
    return counts


async def run_chaos_scenario(speed: float) -> None:
    console.print("[bold cyan]Smart City Dispatch Grid — Earthquake Chaos Simulation[/bold cyan]\n")

    # 1. Reset DB + seed fleet
    console.print("[cyan]Resetting database and seeding fleet...[/cyan]")
    db = ResourceDB()
    await db.drop_tables()
    await db.create_tables()
    await seed_fleet(db)
    console.print("[green]Fleet seeded (16 vehicles).[/green]\n")

    # 2. Initialize agents
    console.print("[cyan]Initializing Triage Agent (loading embedding model)...[/cyan]")
    triage_agent = TriageAgent()
    await triage_agent.initialize()
    dispatch_agent = DispatchAgent(db=db, enable_rerouting=True, enable_llm_reasoning=True)
    console.print("[green]Agents ready.[/green]\n")

    # 3. Build call batch with staggered timestamps
    calls = [
        _make_call(text, offset_sec=i * 30)
        for i, text in enumerate(EARTHQUAKE_CHAOS_TRANSCRIPTS)
    ]
    stream = CallStream.from_batch(calls, speed_multiplier=speed)

    # 4. Start dispatch background loop
    await dispatch_agent.start()

    # 5. Process stream with Live display
    recent_triages: list[TriageResult] = []
    recent_decisions: list[DispatchDecision] = []
    call_count = 0
    sim_start = time.perf_counter()

    with Live(console=console, refresh_per_second=2, transient=False) as live:
        async for call in stream:
            call_count += 1
            result = await triage_agent.process(call)
            recent_triages.append(result)

            decision = await dispatch_agent.process(result)
            if decision:
                recent_decisions.append(decision)

            fleet_counts = await get_fleet_counts(db)
            live.update(_build_live_panel(call_count, recent_triages, recent_decisions, fleet_counts))

    # 6. Wait for background dispatches to settle
    console.print("\n[dim]Waiting 5s for background dispatch cycles to settle...[/dim]")
    await asyncio.sleep(5)
    await dispatch_agent.stop()

    sim_elapsed = time.perf_counter() - sim_start

    # 7. Final summary
    all_incidents = await db.list_incidents()
    all_logs = await db.list_dispatch_logs()
    fleet_counts = await get_fleet_counts(db)
    ds = dispatch_agent.stats()
    ts = triage_agent.stats()

    dup_count = sum(1 for t in recent_triages if t.is_duplicate)
    unique_count = len(recent_triages) - dup_count

    summary = (
        f"[bold]Total calls:[/bold]          {call_count}\n"
        f"[bold]Unique incidents:[/bold]      {unique_count}\n"
        f"[bold]Duplicates detected:[/bold]   [yellow]{dup_count}[/yellow]\n"
        f"[bold]DB incidents:[/bold]          {len(all_incidents)}\n\n"
        f"[bold]Dispatch decisions:[/bold]    {ds['total_decisions']}\n"
        f"[bold]By status:[/bold]             {ds['by_status']}\n"
        f"[bold]Reassignments:[/bold]         [cyan]{ds['reassignments']}[/cyan]\n"
        f"[bold]Dispatch logs:[/bold]         {len(all_logs)}\n"
        f"[bold]Avg dispatch time:[/bold]     {ds['avg_processing_ms']}ms\n\n"
        f"[bold]Fleet at end:[/bold]          {fleet_counts}\n"
        f"[bold]Total sim time:[/bold]        {sim_elapsed:.1f}s"
    )
    console.print(Panel(summary, title="[bold]Earthquake Chaos — Final Summary[/bold]", border_style="blue"))

    # Reassignment events
    events = dispatch_agent.reassignment_events()
    if events:
        console.print(f"\n[bold cyan]Reassignment Events ({len(events)}):[/bold cyan]")
        for ev in events:
            console.print(
                f"  [cyan]{ev.resource_id}[/cyan]: {ev.from_incident_id} → {ev.to_incident_id} | {ev.reason}"
            )

    await db.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run a full dispatch simulation scenario.")
    parser.add_argument("--scenario", type=str, default="earthquake_chaos", help="Scenario name")
    parser.add_argument(
        "--speed",
        type=float,
        default=100.0,
        help="Speed multiplier for replay (default 100x = ~4.5s for 15 calls at 30s intervals)",
    )
    args = parser.parse_args()

    if args.scenario != "earthquake_chaos":
        console.print(f"[red]Unknown scenario '{args.scenario}'. Available: earthquake_chaos[/red]")
        sys.exit(1)

    await run_chaos_scenario(speed=args.speed)


if __name__ == "__main__":
    asyncio.run(main())
