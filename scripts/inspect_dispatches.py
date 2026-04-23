"""Inspect dispatch history from the database.

Shows timeline of dispatches, reassignments, and per-vehicle utilization.

Usage:
  python scripts/inspect_dispatches.py
  python scripts/inspect_dispatches.py --db dispatch.db
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smart_dispatch.data.resource_db import ResourceDB

console = Console()


async def run_inspect(db_url: str) -> None:
    db = ResourceDB(db_url=f"sqlite+aiosqlite:///{db_url}")

    # Load all data
    incidents = await db.list_incidents()
    logs = await db.list_dispatch_logs()
    resources = await db.list_resources()

    if not incidents:
        console.print("[yellow]No incidents found in database. Run a simulation first.[/yellow]")
        await db.close()
        return

    # -------- Incidents table --------
    inc_table = Table(title=f"Incidents ({len(incidents)})", show_lines=True)
    inc_table.add_column("ID", style="dim yellow", width=14)
    inc_table.add_column("Type", width=10)
    inc_table.add_column("Severity", width=10)
    inc_table.add_column("Node", width=6)
    inc_table.add_column("Status", width=20)
    inc_table.add_column("Dup calls", justify="right", width=8)
    inc_table.add_column("Created", width=20)

    for inc in incidents:
        sev_style = {
            "CRITICAL": "bold red", "HIGH": "bold yellow", "MEDIUM": "yellow", "LOW": "dim"
        }.get(inc.severity, "")
        status_style = "green" if inc.status == "dispatched" else (
            "yellow" if inc.status == "partially_dispatched" else "red"
        )
        inc_table.add_row(
            inc.id, inc.incident_type, f"[{sev_style}]{inc.severity}[/{sev_style}]",
            inc.location_node_id or "?",
            f"[{status_style}]{inc.status}[/{status_style}]",
            str(inc.duplicate_call_count),
            inc.created_at.strftime("%H:%M:%S") if inc.created_at else "?",
        )
    console.print(inc_table)

    # -------- Dispatch timeline --------
    if logs:
        log_table = Table(title=f"Dispatch Log Timeline ({len(logs)})", show_lines=True)
        log_table.add_column("#", width=4, justify="right")
        log_table.add_column("Time", width=10)
        log_table.add_column("Resource", width=12)
        log_table.add_column("Incident", width=14)
        log_table.add_column("ETA (min)", justify="right", width=10)
        log_table.add_column("Reassigned", width=10, justify="center")

        for i, log in enumerate(logs, 1):
            log_table.add_row(
                str(i),
                log.dispatched_at.strftime("%H:%M:%S") if log.dispatched_at else "?",
                log.resource_id,
                log.incident_id,
                f"{log.travel_time_sec / 60:.1f}",
                "[cyan]YES[/cyan]" if log.reassigned else "—",
            )
        console.print(log_table)
    else:
        console.print("[dim]No dispatch logs found.[/dim]")

    # -------- Per-vehicle utilization --------
    util: dict[str, int] = {}
    for log in logs:
        util[log.resource_id] = util.get(log.resource_id, 0) + 1

    if util:
        util_table = Table(title="Vehicle Utilization", show_lines=False)
        util_table.add_column("Resource ID", style="cyan", width=12)
        util_table.add_column("Call Sign", width=20)
        util_table.add_column("Dispatches", justify="right", width=12)
        util_table.add_column("Current Status", width=16)

        res_map = {r.id: r for r in resources}
        for rid, count in sorted(util.items(), key=lambda x: -x[1]):
            res = res_map.get(rid)
            call_sign = res.call_sign if res else "—"
            status = res.status.value if res else "?"
            status_style = "green" if status == "available" else "yellow"
            util_table.add_row(
                rid, call_sign, str(count), f"[{status_style}]{status}[/{status_style}]"
            )
        console.print(util_table)

    # -------- Summary panel --------
    reassign_count = sum(1 for log in logs if log.reassigned)
    avg_eta = sum(log.travel_time_sec for log in logs) / len(logs) / 60 if logs else 0
    summary = (
        f"[bold]Incidents:[/bold]         {len(incidents)}\n"
        f"[bold]Dispatch logs:[/bold]     {len(logs)}\n"
        f"[bold]Reassignments:[/bold]     {reassign_count}\n"
        f"[bold]Avg ETA:[/bold]           {avg_eta:.1f} min\n"
        f"[bold]Vehicles used:[/bold]     {len(util)}/{len(resources)}"
    )
    console.print(Panel(summary, title="Summary", border_style="blue"))

    await db.close()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect dispatch history from the database.")
    parser.add_argument("--db", type=str, default="dispatch.db", help="SQLite DB file path")
    args = parser.parse_args()
    await run_inspect(args.db)


if __name__ == "__main__":
    asyncio.run(main())
