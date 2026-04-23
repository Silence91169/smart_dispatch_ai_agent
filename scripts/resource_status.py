"""Display current resource fleet status from the dispatch database."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.live import Live
from rich.table import Table

from smart_dispatch.data.city_fixtures import get_location_by_node_id
from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus

console = Console()

_STATUS_COLOURS = {
    ResourceStatus.AVAILABLE: "green",
    ResourceStatus.DISPATCHED: "yellow",
    ResourceStatus.EN_ROUTE: "cyan",
    ResourceStatus.ON_SCENE: "bright_cyan",
    ResourceStatus.RETURNING: "blue",
    ResourceStatus.OUT_OF_SERVICE: "red",
}


def _node_name(node_id: str) -> str:
    loc = get_location_by_node_id(node_id)
    return loc["name"] if loc else node_id


async def _fetch_table(db: ResourceDB) -> Table:
    resources = await db.list_resources()

    counts = {s: 0 for s in ResourceStatus}
    for r in resources:
        counts[r.status] += 1

    available = counts[ResourceStatus.AVAILABLE]
    total = len(resources)

    table = Table(
        title=f"[bold]Resource Fleet Status[/bold]  — {available}/{total} available",
        show_lines=True,
        expand=True,
    )
    table.add_column("ID", style="dim yellow", width=10)
    table.add_column("Call Sign", style="cyan", width=16)
    table.add_column("Type", width=12)
    table.add_column("Status", width=14)
    table.add_column("Location", width=26)
    table.add_column("Incident", width=14)
    table.add_column("ETA (s)", justify="right", width=8)
    table.add_column("Dispatches", justify="right", width=10)

    for r in sorted(resources, key=lambda x: x.id):
        colour = _STATUS_COLOURS.get(r.status, "white")
        eta = f"{int(r.eta_to_destination_sec)}" if r.eta_to_destination_sec else "—"
        incident = r.current_incident_id or "—"
        location = f"{r.current_node_id} {_node_name(r.current_node_id)}"
        table.add_row(
            r.id,
            r.call_sign,
            r.resource_type,
            f"[{colour}]{r.status.value}[/{colour}]",
            location,
            incident,
            eta,
            str(r.total_dispatches),
        )
    return table


async def run(db_url: str, once: bool, refresh_sec: float) -> None:
    db = ResourceDB(db_url=db_url)

    if once:
        table = await _fetch_table(db)
        console.print(table)
    else:
        with Live(console=console, refresh_per_second=1, screen=False) as live:
            try:
                while True:
                    table = await _fetch_table(db)
                    live.update(table)
                    await asyncio.sleep(refresh_sec)
            except KeyboardInterrupt:
                pass

    await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Show resource fleet status.")
    parser.add_argument("--once", action="store_true", help="Print once and exit")
    parser.add_argument("--refresh", type=float, default=2.0, help="Refresh interval in seconds")
    parser.add_argument(
        "--db-path",
        default="sqlite+aiosqlite:///./dispatch.db",
        help="SQLAlchemy async DB URL",
    )
    args = parser.parse_args()
    asyncio.run(run(db_url=args.db_path, once=args.once, refresh_sec=args.refresh))


if __name__ == "__main__":
    main()
