"""Measure dedup quality against golden dataset duplicate pairs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from smart_dispatch.agents.triage import TriageAgent
from smart_dispatch.data.golden_dataset import load_golden_dataset

console = Console()


async def run_benchmark() -> None:
    cases = load_golden_dataset()

    # Build ground-truth duplicate map: call_id → primary call_id
    gt_duplicates: dict[str, str] = {}
    for case in cases:
        if case.expected.is_duplicate_of:
            gt_duplicates[case.call.call_id] = case.expected.is_duplicate_of

    console.print(f"[cyan]Golden cases:[/cyan] {len(cases)}")
    console.print(f"[cyan]Ground-truth duplicate pairs:[/cyan] {len(gt_duplicates)}\n")

    console.print("[cyan]Initializing Triage Agent...[/cyan]")
    agent = TriageAgent()
    await agent.initialize()
    console.print("[green]Ready. Processing cases in order...[/green]\n")

    # Track predictions
    predicted_dup: dict[str, bool] = {}     # call_id → True if agent flagged as dup
    predicted_of: dict[str, str] = {}       # call_id → primary call_id if dup

    sim_correct: list[float] = []
    sim_missed: list[float] = []

    for case in cases:
        result = await agent.process(case.call)
        predicted_dup[case.call.call_id] = result.is_duplicate
        if result.is_duplicate and result.duplicate_of_call_id:
            predicted_of[case.call.call_id] = result.duplicate_of_call_id

    # Evaluate
    true_positives = 0
    false_negatives = 0
    false_positives = 0
    detail_rows = []

    for case in cases:
        cid = case.call.call_id
        is_gt_dup = cid in gt_duplicates
        is_pred_dup = predicted_dup.get(cid, False)

        if is_gt_dup and is_pred_dup:
            true_positives += 1
            sim = agent.deduplicator._records  # not available post-facto; use table note
            detail_rows.append((cid, gt_duplicates[cid], predicted_of.get(cid, "?"), "✓ TP", "green"))
        elif is_gt_dup and not is_pred_dup:
            false_negatives += 1
            detail_rows.append((cid, gt_duplicates[cid], "—", "✗ FN", "red"))
        elif not is_gt_dup and is_pred_dup:
            false_positives += 1
            detail_rows.append((cid, "—", predicted_of.get(cid, "?"), "! FP", "yellow"))

    total_pairs = len(gt_duplicates)
    unique_total = len(cases) - total_pairs

    table = Table(title="Dedup Benchmark Detail", show_lines=True)
    table.add_column("Call ID", style="dim yellow", width=14)
    table.add_column("GT Primary", width=14)
    table.add_column("Pred Primary", width=14)
    table.add_column("Result", width=8, justify="center")

    for cid, gt_p, pred_p, label, colour in detail_rows:
        table.add_row(cid, gt_p, pred_p, f"[{colour}]{label}[/{colour}]")

    console.print(table)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / total_pairs if total_pairs > 0 else 0.0

    summary = (
        f"[bold]Total duplicate pairs (GT):[/bold]  {total_pairs}\n"
        f"[bold]Correctly detected (TP):[/bold]     [green]{true_positives}[/green] "
        f"({100*true_positives//max(total_pairs,1)}%)\n"
        f"[bold]Missed (FN):[/bold]                 [red]{false_negatives}[/red] "
        f"({100*false_negatives//max(total_pairs,1)}%)\n"
        f"[bold]False positives (FP):[/bold]        [yellow]{false_positives}[/yellow] "
        f"({100*false_positives//max(unique_total,1)}%)\n\n"
        f"[bold]Precision:[/bold] {precision:.2f}  |  [bold]Recall:[/bold] {recall:.2f}\n\n"
        f"[bold]Dedup settings:[/bold] "
        f"threshold={agent.deduplicator.similarity_threshold} | "
        f"window={agent.deduplicator.stats()['time_window_minutes']}min\n"
        f"[bold]Agent stats:[/bold] processed={agent.call_count} | "
        f"index_size={agent.deduplicator.stats()['index_size']}"
    )

    console.print(Panel(summary, title="Dedup Benchmark Results", border_style="blue"))

    if false_negatives > 0:
        console.print(
            "\n[dim]Tip: lower the threshold (e.g. 0.70) to catch missed pairs. "
            "Watch false positives — they cause wrong dedup.[/dim]"
        )


if __name__ == "__main__":
    asyncio.run(run_benchmark())
