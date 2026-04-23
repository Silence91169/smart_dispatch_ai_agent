"""Initialise the dispatch database and seed the vehicle fleet."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table

from smart_dispatch.data.resource_db import ResourceDB, ResourceStatus
from smart_dispatch.data.resource_seeder import seed_fleet

console = Console()


async def run(db_url: str, reset: bool) -> None:
    db = ResourceDB(db_url=db_url)

    if reset:
        console.print("[yellow]Dropping existing tables...[/yellow]")
        await db.drop_tables()

    console.print("[cyan]Creating tables...[/cyan]")
    await db.create_tables()

    console.print("[cyan]Seeding fleet...[/cyan]")
    resources = await seed_fleet(db)

    table = Table(title="Seeded Fleet", show_lines=True)
    table.add_column("ID", style="dim yellow")
    table.add_column("Call Sign", style="cyan")
    table.add_column("Type")
    table.add_column("Home Node")
    table.add_column("Status", style="green")

    for r in resources:
        table.add_row(r.id, r.call_sign, r.resource_type, r.home_node_id, r.status.value)

    console.print(table)
    console.print(f"\n[bold green]Done — {len(resources)} vehicles seeded.[/bold green]")
    await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise dispatch DB and seed fleet.")
    parser.add_argument("--reset", action="store_true", help="Drop tables before recreating")
    parser.add_argument(
        "--db-path",
        default="sqlite+aiosqlite:///./dispatch.db",
        help="SQLAlchemy async DB URL",
    )
    args = parser.parse_args()
    asyncio.run(run(db_url=args.db_path, reset=args.reset))


if __name__ == "__main__":
    main()
