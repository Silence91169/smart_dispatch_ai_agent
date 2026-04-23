"""Live streaming demo — watch mock 911 calls arrive in real time."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from smart_dispatch.data.call_generator import MockCallGenerator
from smart_dispatch.data.call_stream import CallStream
from smart_dispatch.data.schemas import MockCall

_FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "incident_scenarios.json"
console = Console()

# Keyword → colour mapping for visual severity hints (not real triage)
_FIRE_WORDS = {"fire", "flame", "burning", "smoke", "engulfed"}
_MEDICAL_WORDS = {"breathing", "unconscious", "pulse", "collapsed", "choking", "bleeding", "cardiac"}
_CRIME_WORDS = {"gun", "knife", "robbery", "stabbed", "shot", "assault", "attack"}
_HAZARD_WORDS = {"gas", "chemical", "leak", "wire", "flood", "hazmat"}


def _guess_colour(transcript: str) -> str:
    words = set(transcript.lower().split())
    if words & _CRIME_WORDS:
        return "red"
    if words & _FIRE_WORDS:
        return "bright_red"
    if words & _MEDICAL_WORDS:
        return "yellow"
    if words & _HAZARD_WORDS:
        return "magenta"
    return "white"


def _build_table(calls: list[MockCall], total: int) -> Table:
    table = Table(
        title=f"[bold]Smart Dispatch — Live Feed[/bold]  ({total} calls streamed)",
        show_lines=True,
        expand=True,
    )
    table.add_column("Time", style="cyan", width=9, no_wrap=True)
    table.add_column("Call ID", style="dim yellow", width=14, no_wrap=True)
    table.add_column("Hint", width=8, no_wrap=True)
    table.add_column("Transcript preview")

    for call in calls[-20:]:  # show last 20
        ts = call.timestamp.strftime("%H:%M:%S")
        colour = _guess_colour(call.transcript)
        hint_labels = {
            "red": "CRIME",
            "bright_red": "FIRE",
            "yellow": "MEDICAL",
            "magenta": "HAZARD",
            "white": "OTHER",
        }
        hint = Text(hint_labels.get(colour, "OTHER"), style=f"bold {colour}")
        preview = call.transcript[:100] + ("…" if len(call.transcript) > 100 else "")
        table.add_row(ts, call.call_id, hint, Text(preview, style=colour))

    return table


def _load_scenario(name: str) -> dict:
    data = json.loads(_FIXTURES.read_text())
    for scenario in data["scenarios"]:
        if scenario["name"] == name:
            return scenario
    names = [s["name"] for s in data["scenarios"]]
    console.print(f"[red]Unknown scenario '{name}'. Available: {', '.join(names)}[/red]")
    sys.exit(1)


async def run_stream(stream: CallStream) -> None:
    calls: list[MockCall] = []
    total = 0

    with Live(console=console, refresh_per_second=4, screen=False) as live:
        async for call in stream:
            calls.append(call)
            total += 1
            live.update(_build_table(calls, total))

    console.print(f"\n[bold green]Stream complete — {total} calls received.[/bold green]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream mock 911 calls in real time with a live terminal display."
    )
    parser.add_argument("--scenario", type=str, default=None, help="Named scenario to replay")
    parser.add_argument("--rate", type=float, default=20.0, help="Calls per minute (live mode)")
    parser.add_argument("--count", type=int, default=15, help="Number of calls to stream (live mode)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--speed",
        type=float,
        default=10.0,
        help="Speed multiplier for scenario replay (default 10 = 10× faster)",
    )
    args = parser.parse_args()

    if args.scenario:
        scenario = _load_scenario(args.scenario)
        console.print(
            Panel(
                f"[bold]{scenario['name']}[/bold]\n{scenario['description']}\n"
                f"[dim]{scenario['total_calls']} calls · {scenario['duplicate_ratio']*100:.0f}%% dupes · "
                f"{scenario['time_window_minutes']} min window · {args.speed}× speed[/dim]",
                title="Scenario",
                border_style="blue",
            )
        )
        gen = MockCallGenerator(seed=scenario["seed"])
        batch = gen.generate_batch(
            total_calls=scenario["total_calls"],
            duplicate_ratio=scenario["duplicate_ratio"],
            template_mix=scenario.get("template_mix"),
            time_window_minutes=scenario["time_window_minutes"],
        )
        stream = CallStream.from_batch(batch, speed_multiplier=args.speed)
    else:
        console.print(
            Panel(
                f"Live mode — [cyan]{args.rate} calls/min[/cyan] · max [cyan]{args.count}[/cyan] calls",
                title="Stream Config",
                border_style="blue",
            )
        )
        gen = MockCallGenerator(seed=args.seed)
        stream = CallStream(
            generator=gen,
            calls_per_minute=args.rate,
            max_calls=args.count,
        )

    asyncio.run(run_stream(stream))


if __name__ == "__main__":
    main()
