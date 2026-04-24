"""CLI entry point: python -m evaluation.run_eval [--limit N] [--output DIR]"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from rich.console import Console

from .evaluator import run_evaluation
from .report import save_report, render_markdown


async def main(args: argparse.Namespace) -> None:
    console = Console()

    # Gracefully handle missing API keys
    has_key = any(
        os.getenv(k) for k in ("GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")
    )
    if not has_key:
        console.print(
            "[bold red]Error:[/bold red] No LLM API key found.\n"
            "Set one of: GROQ_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in your .env file.\n"
            "Example:  [cyan]GROQ_API_KEY=gsk_xxx[/cyan]"
        )
        sys.exit(1)

    console.print(f"[bold cyan]Running evaluation (limit={args.limit or 'all'})...[/bold cyan]")

    with console.status("[bold cyan]Processing golden cases..."):
        report = await run_evaluation(limit=args.limit)

    md = render_markdown(report)
    console.print(md)

    if args.output:
        out_dir = Path(args.output)
        md_path, json_path = save_report(report, out_dir)
        console.print(
            f"\n[green]✓[/green] Saved to [cyan]{md_path}[/cyan] and [cyan]{json_path}[/cyan]"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation on the golden dataset")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases")
    parser.add_argument("--output", type=str, default="reports/", help="Output directory")
    args = parser.parse_args()
    asyncio.run(main(args))
