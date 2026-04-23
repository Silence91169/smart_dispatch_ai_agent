"""CLI script to generate and dump mock 112 calls."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.schemas import MockCall

_FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "incident_scenarios.json"
console = Console()


def _load_scenario(name: str) -> dict:
    data = json.loads(_FIXTURES.read_text())
    for scenario in data["scenarios"]:
        if scenario["name"] == name:
            return scenario
    names = [s["name"] for s in data["scenarios"]]
    console.print(f"[red]Unknown scenario '{name}'. Available: {', '.join(names)}[/red]")
    sys.exit(1)


def _print_table(calls: list[MockCall]) -> None:
    table = Table(title=f"Generated Calls ({len(calls)} total)", show_lines=True)
    table.add_column("Time", style="cyan", width=8)
    table.add_column("Call ID", style="yellow", width=14)
    table.add_column("Event ID", style="dim", width=30)
    table.add_column("Preview", style="white")

    for call in calls:
        ts = call.timestamp.strftime("%H:%M:%S")
        preview = call.transcript[:80] + ("…" if len(call.transcript) > 80 else "")
        table.add_row(ts, call.call_id, call.event_id or "—", preview)

    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate mock 112 call transcripts for the Smart Dispatch system."
    )
    parser.add_argument("--count", type=int, default=10, help="Number of calls to generate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--output", type=Path, default=None, help="Write JSON to this file")
    parser.add_argument("--scenario", type=str, default=None, help="Use a named scenario from fixtures")
    parser.add_argument("--pretty", action="store_true", help="Print rich table to stdout")
    parser.add_argument(
        "--duplicate-ratio",
        type=float,
        default=0.3,
        help="Fraction of duplicate calls (0–1, default 0.3)",
    )
    args = parser.parse_args()

    if args.scenario:
        scenario = _load_scenario(args.scenario)
        gen = MockCallGenerator(seed=scenario["seed"])
        calls = gen.generate_batch(
            total_calls=scenario["total_calls"],
            duplicate_ratio=scenario["duplicate_ratio"],
            template_mix=scenario.get("template_mix"),
            time_window_minutes=scenario["time_window_minutes"],
        )
    else:
        gen = MockCallGenerator(seed=args.seed)
        calls = gen.generate_batch(
            total_calls=args.count,
            duplicate_ratio=args.duplicate_ratio,
        )

    if args.pretty or (not args.output and not args.scenario):
        _print_table(calls)
    elif not args.output:
        _print_table(calls)

    if args.output:
        serialised = [
            json.loads(call.model_dump_json())
            for call in calls
        ]
        args.output.write_text(json.dumps(serialised, indent=2, default=str))
        console.print(f"[green]Wrote {len(calls)} calls to {args.output}[/green]")
    elif not args.pretty and not args.scenario:
        pass
    else:
        # If --scenario was used without --output, also dump JSON to stdout
        if args.scenario and not args.pretty:
            serialised = [json.loads(c.model_dump_json()) for c in calls]
            print(json.dumps(serialised, indent=2, default=str))


if __name__ == "__main__":
    main()
