"""Print the Delhi city graph — nodes, edges, stats, and optional pathfinding."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smart_dispatch.data.city_graph import CityGraph
from smart_dispatch.data.city_fixtures import get_location_by_node_id

console = Console()


def _node_name(node_id: str) -> str:
    loc = get_location_by_node_id(node_id)
    return loc["name"] if loc else node_id


def show_nodes(g: CityGraph) -> None:
    table = Table(title="Delhi City Nodes", show_lines=True)
    table.add_column("Node ID", style="dim yellow", width=8)
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Lat", justify="right")
    table.add_column("Lng", justify="right")
    table.add_column("Degree", justify="right")

    for node_id, data in sorted(g.graph.nodes(data=True)):
        table.add_row(
            node_id,
            data.get("name", ""),
            data.get("landmark_type", ""),
            f"{data.get('lat', 0):.4f}",
            f"{data.get('lng', 0):.4f}",
            str(g.graph.degree(node_id)),
        )
    console.print(table)


def show_edges(g: CityGraph) -> None:
    table = Table(title="Delhi Road Edges", show_lines=True)
    table.add_column("From", style="cyan", width=22)
    table.add_column("To", style="cyan", width=26)
    table.add_column("Travel Time", justify="right")
    table.add_column("Distance (km)", justify="right")
    table.add_column("Road Type")

    for u, v, data in sorted(g.graph.edges(data=True)):
        table.add_row(
            f"{u} {_node_name(u)}",
            f"{v} {_node_name(v)}",
            f"{data['travel_time_sec']}s ({data['travel_time_sec']//60}m)",
            f"{data['distance_km']:.1f}",
            data.get("road_type", ""),
        )
    console.print(table)


def show_stats(g: CityGraph) -> None:
    s = g.stats()
    console.print(
        Panel(
            f"Nodes: [cyan]{s['nodes']}[/cyan]  |  "
            f"Edges: [cyan]{s['edges']}[/cyan]  |  "
            f"Connected: [{'green' if s['connected'] else 'red'}]{s['connected']}[/{'green' if s['connected'] else 'red'}]  |  "
            f"Avg degree: [cyan]{s['avg_degree']}[/cyan]",
            title="Graph Stats",
            border_style="blue",
        )
    )


def show_path(g: CityGraph, from_node: str, to_node: str) -> None:
    try:
        path = g.shortest_path(from_node, to_node)
        total_sec = g.travel_time(from_node, to_node)
        mins, secs = divmod(int(total_sec), 60)

        table = Table(title=f"Shortest Path: {from_node} → {to_node}", show_lines=True)
        table.add_column("Step", justify="right", width=5)
        table.add_column("Node", style="dim yellow", width=6)
        table.add_column("Name", style="cyan")

        for i, node in enumerate(path):
            table.add_row(str(i + 1), node, _node_name(node))

        console.print(table)
        console.print(
            f"Total travel time: [bold cyan]{mins}m {secs}s[/bold cyan] "
            f"({int(total_sec)}s)  |  Hops: {len(path) - 1}"
        )
    except Exception as exc:
        console.print(f"[red]Path error: {exc}[/red]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualise the Delhi city graph.")
    parser.add_argument("--nodes", action="store_true", help="Show node table")
    parser.add_argument("--edges", action="store_true", help="Show edge table")
    parser.add_argument("--stats", action="store_true", help="Show graph statistics")
    parser.add_argument("--from", dest="from_node", help="Source node for pathfinding")
    parser.add_argument("--to", dest="to_node", help="Destination node for pathfinding")
    args = parser.parse_args()

    g = CityGraph()

    # Default: show everything
    show_all = not any([args.nodes, args.edges, args.stats, args.from_node, args.to_node])

    if show_all or args.stats:
        show_stats(g)
    if show_all or args.nodes:
        show_nodes(g)
    if show_all or args.edges:
        show_edges(g)
    if args.from_node and args.to_node:
        show_path(g, args.from_node, args.to_node)
    elif args.from_node or args.to_node:
        console.print("[red]Provide both --from and --to for pathfinding.[/red]")


if __name__ == "__main__":
    main()
