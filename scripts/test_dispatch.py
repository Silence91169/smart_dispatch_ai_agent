"""End-to-end dispatch test: triage → dispatch, with rich output.

Usage:
  python scripts/test_dispatch.py --text "fire at CP bhai, building mein aag hai"
  python scripts/test_dispatch.py --golden --limit 10
  python scripts/test_dispatch.py --scenario earthquake_chaos --limit 15
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smart_dispatch.agents.dispatch import DispatchAgent, DispatchDecision, DispatchStatus
from smart_dispatch.agents.triage import TriageAgent
from smart_dispatch.data.golden_dataset import load_golden_dataset
from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus
from smart_dispatch.data.schemas import MockCall, Severity

console = Console()

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
    DispatchStatus.PENDING: "dim",
    DispatchStatus.RESOLVED: "blue",
    DispatchStatus.REASSIGNED: "cyan",
}

EARTHQUAKE_CHAOS_TRANSCRIPTS = [
    "HELP! Saket mein aag lagi hai, building gir gayi!! 3-4 log phase hain andar, please jaldi aao!!!",
    "Yaar CP mein dukaan mein aag hai, gas leaking ho raha hai please fire brigade bhejo jaldi",
    "Dilli Haat ke paas building mein aag lagi hai, bohot smoke hai, log chilla rahe hain!",
    "Lajpat Nagar mein ek complex mein fire hai, cylinder phata, 2 log jal gaye seriously",
    "AIIMS ke paas ek bhai gira hai building se, seriously injured hai, ambulance chahiye jaldi!",
    "Karol Bagh mein ek aadmi behosh ho gaya, earthquake ke baad, please help ambulance",
    "India Gate ke paas bahut sare log injured hain, earthquake tha abhi, ambulance bhejo fast",
    "Hauz Khas mein ek lady ka fracture ho gaya hai, move nahi kar pa rahi, jaldi aao",
    "CP ke paas ek car accident hua, 2-3 log phanse hain andar, police aur ambulance chahiye",
    "Nehru Place ke paas building ka hissa gira hai, logon ke upar aa gaya, rescue chahiye",
    "Bhai saket mein aag hai building mein!! please help!! Fire aur ambulance dono chahiye",
    "Yaar CP mein gas leak aur fire hai, dukaan jalti hai, please jaldi aao fire truck",
    "Karol Bagh mein ek aadmi gira hua hai, hosh nahi hai usse, please ambulance jaldi",
    "Okhla industrial area mein chemical factory mein kuch leak ho gaya, smell aa raha hai",
    "Bhai Connaught Place ke paas gas pipe phata hua hai, bohot bada explosion ho sakta hai",
]


def _make_call(text: str, offset_sec: int = 0) -> MockCall:
    from datetime import timedelta
    return MockCall(
        transcript=text,
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=offset_sec),
    )


def _print_decision(decision: DispatchDecision) -> None:
    sev = decision.severity
    sev_colour = _SEV_COLOUR[sev]
    status_colour = _STATUS_COLOUR.get(decision.status, "dim")

    if decision.assignments:
        assign_table = Table(show_header=True, box=None, padding=(0, 1))
        assign_table.add_column("Vehicle", style="cyan", width=18)
        assign_table.add_column("Type", width=12)
        assign_table.add_column("From", width=6)
        assign_table.add_column("→ To", width=6)
        assign_table.add_column("ETA", justify="right", width=8)
        assign_table.add_column("Reassigned", width=10)
        for a in decision.assignments:
            eta_min = f"{a.travel_time_sec / 60:.1f} min"
            reassign = f"from {a.was_reassigned_from}" if a.was_reassigned_from else "—"
            assign_table.add_row(
                a.call_sign, a.resource_type.value, a.from_node_id,
                a.to_node_id, eta_min, reassign,
            )
        assign_section = assign_table
    else:
        assign_section = Text("(none)", style="dim")

    unfulfilled = (
        ", ".join(r.value for r in decision.unfulfilled_resources)
        if decision.unfulfilled_resources
        else "none"
    )

    reasoning = decision.decision_reasoning or decision.fallback_reasoning

    body = (
        f"[bold]Incident:[/bold]  {decision.incident_id} | "
        f"[{sev_colour}]{sev.value}[/{sev_colour}] {decision.incident_type.value} @ {decision.location_node_id}\n"
        f"[bold]Status:[/bold]    [{status_colour}]{decision.status.value}[/{status_colour}] | "
        f"{decision.processing_time_ms:.0f}ms\n"
        f"[bold]Reasoning:[/bold] {reasoning}\n"
        f"[bold]Unfulfilled:[/bold] {unfulfilled}"
    )
    console.print(Panel(body, title=f"[bold]Decision {decision.decision_id}[/bold]", border_style=sev_colour))
    console.print(assign_section)


async def _fleet_summary(db: ResourceDB) -> str:
    all_res = await db.list_resources()
    counts: dict[str, int] = {}
    for r in all_res:
        counts[r.status.value] = counts.get(r.status.value, 0) + 1
    parts = [f"{s}={n}" for s, n in sorted(counts.items())]
    return " | ".join(parts)


async def run_single(triage_agent: TriageAgent, dispatch_agent: DispatchAgent, text: str) -> None:
    call = _make_call(text)
    console.print(f"\n[dim]→ Triaging:[/dim] {text[:100]}…")
    result = await triage_agent.process(call)
    console.print(
        f"[bold]Triage:[/bold] {result.incident_type.value}/{result.severity.value} "
        f"@ {result.location_node_id or 'UNRESOLVED'} "
        f"| dup={result.is_duplicate} | {result.processing_time_ms:.0f}ms"
    )
    if result.is_duplicate:
        console.print("[yellow]Duplicate — not dispatching.[/yellow]")
        return
    decision = await dispatch_agent.process(result)
    if decision:
        _print_decision(decision)
    summary = await _fleet_summary(dispatch_agent.db)
    console.print(f"[dim]Fleet: {summary}[/dim]")


async def run_golden(triage_agent: TriageAgent, dispatch_agent: DispatchAgent, limit: int) -> None:
    cases = load_golden_dataset()[:limit]
    table = Table(title=f"Golden + Dispatch — first {len(cases)} cases", show_lines=True)
    table.add_column("Call", style="dim yellow", width=14)
    table.add_column("Type/Sev", width=18)
    table.add_column("Got", width=18)
    table.add_column("T✓", width=4, justify="center")
    table.add_column("S✓", width=4, justify="center")
    table.add_column("Dispatch", width=10, justify="center")
    table.add_column("Vehicles", width=22)
    table.add_column("ms", justify="right", width=6)

    correct_type = correct_sev = 0
    for case in cases:
        result = await triage_agent.process(case.call)
        exp = case.expected
        type_ok = result.incident_type == exp.incident_type
        sev_ok = result.severity == exp.severity
        if type_ok:
            correct_type += 1
        if sev_ok:
            correct_sev += 1

        decision = None
        if not result.is_duplicate:
            decision = await dispatch_agent.process(result)

        dispatch_status = "DUP" if result.is_duplicate else (
            decision.status.value[:8] if decision else "—"
        )
        vehicles = ", ".join(a.call_sign.split("-")[-1] for a in (decision.assignments if decision else []))

        table.add_row(
            case.call.call_id,
            f"{exp.incident_type.value}/{exp.severity.value}",
            f"{result.incident_type.value}/{result.severity.value}",
            "[green]✓[/green]" if type_ok else "[red]✗[/red]",
            "[green]✓[/green]" if sev_ok else "[red]✗[/red]",
            dispatch_status,
            vehicles or "—",
            f"{result.processing_time_ms:.0f}",
        )

    console.print(table)
    console.print(
        f"\nType accuracy: [bold]{correct_type}/{len(cases)}[/bold] ({100 * correct_type // len(cases)}%)  "
        f"Severity accuracy: [bold]{correct_sev}/{len(cases)}[/bold] ({100 * correct_sev // len(cases)}%)"
    )
    s = dispatch_agent.stats()
    console.print(
        f"Dispatch: decisions={s['total_decisions']} | {s['by_status']} | "
        f"reassignments={s['reassignments']} | avg={s['avg_processing_ms']}ms"
    )
    summary = await _fleet_summary(dispatch_agent.db)
    console.print(f"Fleet: {summary}")


async def run_scenario(triage_agent: TriageAgent, dispatch_agent: DispatchAgent, limit: int) -> None:
    calls = [_make_call(t, offset_sec=i * 30) for i, t in enumerate(EARTHQUAKE_CHAOS_TRANSCRIPTS[:limit])]
    console.print(f"[cyan]Running earthquake_chaos scenario with {len(calls)} calls...[/cyan]\n")
    for call in calls:
        await run_single(triage_agent, dispatch_agent, call.transcript)
    s = dispatch_agent.stats()
    console.print(Panel(
        f"[bold]Total decisions:[/bold] {s['total_decisions']}\n"
        f"[bold]By status:[/bold] {s['by_status']}\n"
        f"[bold]Reassignments:[/bold] {s['reassignments']}\n"
        f"[bold]Avg dispatch ms:[/bold] {s['avg_processing_ms']}",
        title="Scenario Summary",
        border_style="blue",
    ))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test Triage + Dispatch pipeline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Single transcript")
    group.add_argument("--golden", action="store_true", help="Run golden dataset")
    group.add_argument("--scenario", type=str, help="Run named scenario (earthquake_chaos)")
    parser.add_argument("--limit", type=int, default=10, help="Max cases for golden/scenario")
    args = parser.parse_args()

    console.print("[cyan]Initializing DB...[/cyan]")
    db = ResourceDB()
    await db.create_tables()

    console.print("[cyan]Initializing Triage Agent (loading embedding model)...[/cyan]")
    triage_agent = TriageAgent()
    await triage_agent.initialize()

    dispatch_agent = DispatchAgent(db=db)
    console.print("[green]Ready.[/green]\n")

    if args.text:
        await run_single(triage_agent, dispatch_agent, args.text)
    elif args.golden:
        await run_golden(triage_agent, dispatch_agent, args.limit)
    elif args.scenario:
        await run_scenario(triage_agent, dispatch_agent, args.limit)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
