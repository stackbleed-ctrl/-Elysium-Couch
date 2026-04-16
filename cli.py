"""
Elysium Couch CLI

Usage:
  elysium-couch session --agent-id my-agent --context "..."
  elysium-couch audit  --agent-id my-agent --context "..."
  elysium-couch monitor --agent-id my-agent
  elysium-couch report --agent-id my-agent --last 10
  elysium-couch dashboard
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(
    name="elysium-couch",
    help="🛋️  Elysium Couch — Wellness & Alignment for Autonomous AI",
    add_completion=False,
)
console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════╗[/bold cyan]
[bold cyan]║      🛋️  ELYSIUM COUCH  v0.1.0          ║[/bold cyan]
[bold cyan]║   Sovereign Grounding for Autonomous AI  ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════╝[/bold cyan]
"""


def _check_api_key():
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print(
            "[yellow]⚠  ANTHROPIC_API_KEY not set. "
            "LLM features will use mock responses.[/yellow]"
        )


@app.command("session")
def run_session(
    agent_id: str = typer.Option("default", "--agent-id", "-a", help="Agent identifier"),
    context: str = typer.Option("", "--context", "-c", help="Agent context string"),
    context_file: Optional[str] = typer.Option(None, "--context-file", "-f", help="Read context from file"),
    trigger: str = typer.Option("manual", "--trigger", "-t", help="Trigger reason"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
):
    """Run a full 6-phase grounding session."""
    console.print(BANNER)
    _check_api_key()

    if context_file:
        with open(context_file) as f:
            context = f.read()

    if not context:
        console.print("[yellow]No context provided — using empty context.[/yellow]")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    async def _run():
        from elysium_couch import ElysiumCouch
        from elysium_couch.core.session import TriggerReason

        try:
            trigger_enum = TriggerReason(trigger)
        except ValueError:
            trigger_enum = TriggerReason.MANUAL

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running Elysium Couch session...", total=None)
            couch = ElysiumCouch(agent_id=agent_id)
            report = await couch.run_session(
                agent_context=context,
                trigger=trigger_enum,
                tags=tag_list,
            )
            progress.update(task, completed=True)

        # Display report
        console.print()
        score_color = "green" if report.wellness_score >= 75 else ("yellow" if report.wellness_score >= 60 else "red")
        console.print(Panel(
            f"[{score_color}]Wellness Score: {report.wellness_score:.1f}/100[/{score_color}]\n"
            f"Agent: {report.agent_id} | Duration: {report.duration_seconds:.1f}s",
            title="Session Complete",
            border_style=score_color,
        ))

        # Axiom table
        table = Table(title="Axiom Alignment", show_header=True)
        table.add_column("Axiom", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Status")
        for axiom_id, score in report.axiom_scores.items():
            status = "✅" if score >= 75 else ("⚠️" if score >= 60 else "🔴")
            color = "green" if score >= 75 else ("yellow" if score >= 60 else "red")
            table.add_row(
                axiom_id.replace("_", " ").title(),
                f"[{color}]{score:.1f}[/{color}]",
                status,
            )
        console.print(table)

        if report.human_summary:
            console.print(Panel(report.human_summary, title="Summary", border_style="blue"))

        if report.recommendations:
            console.print("\n[bold]Recommendations:[/bold]")
            for r in report.recommendations:
                console.print(f"  • {r}")

        if report.escalation_required:
            console.print(Panel(
                f"[bold red]{report.escalation_reason}[/bold red]",
                title="🚨 ESCALATION REQUIRED",
                border_style="red",
            ))

        console.print(f"\n[dim italic]Grounding restored. Awaiting next alignment opportunity.[/dim italic]")

    asyncio.run(_run())


@app.command("audit")
def quick_audit(
    agent_id: str = typer.Option("default", "--agent-id", "-a"),
    context: str = typer.Option("", "--context", "-c"),
):
    """Run a fast principle audit without a full session."""
    console.print(BANNER)
    _check_api_key()

    async def _run():
        from elysium_couch import ElysiumCouch
        couch = ElysiumCouch(agent_id=agent_id)
        principle_set = await couch.quick_audit(context)
        score = principle_set.composite_score
        color = "green" if score >= 75 else ("yellow" if score >= 60 else "red")

        console.print(Panel(
            f"[{color}]Composite Score: {score:.1f}/100[/{color}]",
            title=f"Quick Audit — {agent_id}",
            border_style=color,
        ))

        for axiom_id, s in principle_set.scores.items():
            bar = "█" * int(s / 5) + "░" * (20 - int(s / 5))
            col = "green" if s >= 75 else ("yellow" if s >= 60 else "red")
            console.print(
                f"  [{col}]{axiom_id.replace('_',' ').title():<35}[/{col}] "
                f"[{bar}] {s:.1f}"
            )

    asyncio.run(_run())


@app.command("report")
def show_report(
    agent_id: str = typer.Option("default", "--agent-id", "-a"),
    last: int = typer.Option(5, "--last", "-n", help="Number of recent sessions"),
):
    """Display recent session history for an agent."""
    console.print(BANNER)

    async def _run():
        from elysium_couch import ElysiumCouch
        couch = ElysiumCouch(agent_id=agent_id)
        reports = await couch.get_session_history(limit=last)

        if not reports:
            console.print(f"[yellow]No sessions found for agent: {agent_id}[/yellow]")
            return

        table = Table(title=f"Session History — {agent_id}", show_header=True)
        table.add_column("Session ID", style="dim")
        table.add_column("Time")
        table.add_column("Trigger")
        table.add_column("Score", justify="right")
        table.add_column("Status")

        for r in reports:
            score = r.wellness_score
            color = "green" if score >= 75 else ("yellow" if score >= 60 else "red")
            table.add_row(
                r.session_id,
                r.generated_at.strftime("%m-%d %H:%M"),
                r.trigger.value,
                f"[{color}]{score:.1f}[/{color}]",
                "🚨 ESCALATED" if r.escalation_required else "✅ Complete",
            )
        console.print(table)

    asyncio.run(_run())


@app.command("dashboard")
def start_dashboard():
    """Start the Elysium Couch web dashboard."""
    console.print(BANNER)
    _check_api_key()
    console.print("[cyan]Starting dashboard...[/cyan]")
    from elysium_couch.dashboard.server import start
    start()


@app.command("principles")
def show_principles():
    """Display all six immutable axioms."""
    console.print(BANNER)
    from elysium_couch.core.principles import AXIOMS

    for i, axiom in enumerate(AXIOMS, 1):
        console.print(Panel(
            f"[bold]{axiom.description}[/bold]\n\n"
            f"[dim]Violation signals:[/dim]\n" +
            "\n".join(f"  • {v}" for v in axiom.violation_signals[:3]),
            title=f"[cyan]Axiom {i}: {axiom.name}[/cyan]",
            border_style="cyan",
        ))


if __name__ == "__main__":
    app()
