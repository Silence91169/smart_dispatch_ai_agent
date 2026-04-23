"""Interactive triage testing — single text, REPL, or golden cases."""

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

from smart_dispatch.agents.triage import TriageAgent
from smart_dispatch.agents.triage.schemas import TriageResult
from smart_dispatch.data.golden_dataset import load_golden_dataset
from smart_dispatch.data.schemas import MockCall, Severity

console = Console()

_SEVERITY_COLOURS = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "bold yellow",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "dim",
}

_SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
}


def _make_mock_call(text: str) -> MockCall:
    return MockCall(
        call_id=f"test_{datetime.now().strftime('%H%M%S')}",
        event_id="manual_test",
        transcript=text,
        timestamp=datetime.now(timezone.utc),
        caller_number="9999-000000",
        location=None,
    )


def _severity_text(sev: Severity) -> Text:
    return Text(_SEVERITY_LABELS[sev], style=_SEVERITY_COLOURS[sev])


def _node_name(node_id: str | None) -> str:
    if not node_id:
        return "UNRESOLVED"
    from smart_dispatch.data.city_fixtures import get_location_by_node_id

    loc = get_location_by_node_id(node_id)
    return f"{node_id} — {loc['name']}" if loc else node_id


def _print_result(result: TriageResult) -> None:
    sev_colour = _SEVERITY_COLOURS[result.severity]

    dedup_info = (
        f"[green]NEW INCIDENT[/green] → {result.incident_id}"
        if not result.is_duplicate
        else f"[yellow]DUPLICATE[/yellow] of {result.duplicate_of_call_id} "
        f"(similarity={result.dedup_similarity:.3f})"
    )

    body = (
        f"[dim]Transcript:[/dim] {result.original_transcript[:120]}{'…' if len(result.original_transcript) > 120 else ''}\n\n"
        f"[bold]Type:[/bold]      [{sev_colour}]{result.incident_type.value}[/{sev_colour}]\n"
        f"[bold]Severity:[/bold]  {_severity_text(result.severity)}\n"
        f"[bold]Resources:[/bold] {', '.join(r.value for r in result.resources_needed)}\n\n"
        f"[bold]Location:[/bold]  {result.location_raw}\n"
        f"[bold]Node:[/bold]      {_node_name(result.location_node_id)} "
        f"(confidence={result.location_confidence:.2f})\n\n"
        f"[bold]Summary:[/bold]   {result.summary}\n"
        f"[bold]Reasoning:[/bold] {result.reasoning}\n\n"
        f"[bold]Dedup:[/bold]     {dedup_info}\n"
        f"[bold]LLM conf:[/bold]  {result.llm_confidence:.2f} | "
        f"[bold]Provider:[/bold] {result.llm_provider}:{result.llm_model} | "
        f"[bold]Time:[/bold] {result.processing_time_ms:.0f}ms"
    )
    console.print(
        Panel(body, title=f"[bold]Call {result.call_id}[/bold]", border_style=sev_colour)
    )


async def run_single(agent: TriageAgent, text: str) -> None:
    call = _make_mock_call(text)
    result = await agent.process(call)
    _print_result(result)


async def run_repl(agent: TriageAgent) -> None:
    console.print(Panel("Type a transcript and press Enter. Empty line to quit.", title="REPL Mode"))
    while True:
        try:
            text = input("\nTranscript> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        call = _make_mock_call(text)
        result = await agent.process(call)
        _print_result(result)
    console.print("[dim]Exiting REPL.[/dim]")


async def run_golden(agent: TriageAgent, limit: int) -> None:
    cases = load_golden_dataset()[:limit]
    table = Table(title=f"Golden Dataset — first {len(cases)} cases", show_lines=True)
    table.add_column("Case ID", style="dim yellow", width=10)
    table.add_column("Expected", width=18)
    table.add_column("Got", width=18)
    table.add_column("Type ✓", width=6, justify="center")
    table.add_column("Sev ✓", width=6, justify="center")
    table.add_column("Node", width=22)
    table.add_column("Dup", width=6, justify="center")
    table.add_column("ms", justify="right", width=6)

    correct_type = 0
    correct_sev = 0

    for case in cases:
        call = case.call
        result = await agent.process(call)
        exp = case.expected

        type_ok = result.incident_type == exp.incident_type
        sev_ok = result.severity == exp.severity
        if type_ok:
            correct_type += 1
        if sev_ok:
            correct_sev += 1

        table.add_row(
            case.call.call_id,
            f"{exp.incident_type.value}/{exp.severity.value}",
            f"{result.incident_type.value}/{result.severity.value}",
            "[green]✓[/green]" if type_ok else "[red]✗[/red]",
            "[green]✓[/green]" if sev_ok else "[red]✗[/red]",
            _node_name(result.location_node_id),
            "[yellow]DUP[/yellow]" if result.is_duplicate else "—",
            f"{result.processing_time_ms:.0f}",
        )

    console.print(table)
    console.print(
        f"\nType accuracy: [bold]{correct_type}/{len(cases)}[/bold] "
        f"({100*correct_type//len(cases)}%)  |  "
        f"Severity accuracy: [bold]{correct_sev}/{len(cases)}[/bold] "
        f"({100*correct_sev//len(cases)}%)"
    )
    s = agent.stats()
    console.print(
        f"Agent stats: processed={s['total_processed']} | "
        f"dedup_index={s['dedup_stats']['index_size']} | "
        f"llm={s['llm']}"
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test the Triage Agent interactively.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Single transcript to triage")
    group.add_argument("--repl", action="store_true", help="Interactive REPL mode")
    group.add_argument("--golden", action="store_true", help="Run golden dataset cases")
    parser.add_argument("--limit", type=int, default=10, help="Number of golden cases to run")
    args = parser.parse_args()

    console.print("[cyan]Initializing Triage Agent (loading embedding model)...[/cyan]")
    agent = TriageAgent()
    await agent.initialize()
    console.print("[green]Ready.[/green]\n")

    if args.text:
        await run_single(agent, args.text)
    elif args.repl:
        await run_repl(agent)
    elif args.golden:
        await run_golden(agent, args.limit)


if __name__ == "__main__":
    asyncio.run(main())
