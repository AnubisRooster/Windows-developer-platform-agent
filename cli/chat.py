"""
Rich console chat loop - start_chat(orchestrator) with pretty printing,
command history, /quit, /clear, /plan.
"""

from __future__ import annotations

try:
    import readline  # noqa: F401 - enables history on Unix
except ImportError:
    pass  # readline not available on Windows; install pyreadline for history
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

if TYPE_CHECKING:
    from agent.orchestrator import Orchestrator

console = Console()


def start_chat(orchestrator: "Orchestrator") -> None:
    """
    Start interactive chat loop with Rich console.

    Commands:
        /quit - Exit
        /clear - Clear screen
        /plan <goal> - Create and display action plan
    """
    console.print(Panel("[bold]Windows Developer Platform Agent[/bold]", expand=False))
    console.print("Commands: [cyan]/quit[/cyan] [cyan]/clear[/cyan] [cyan]/plan <goal>[/cyan]")
    console.print()

    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\nBye!")
            break

        if not user_input.strip():
            continue

        # Handle commands
        if user_input.strip().lower().startswith("/quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.strip().lower().startswith("/clear"):
            console.clear()
            continue

        if user_input.strip().lower().startswith("/plan "):
            goal = user_input[6:].strip()
            if not goal:
                console.print("[yellow]Usage: /plan <goal>[/yellow]")
                continue
            try:
                from agent.planner import Planner

                planner = Planner(orchestrator.llm)
                plan = planner.create_plan(goal, orchestrator.tools.list_tools())
                lines = [f"**Goal:** {plan.goal}", ""]
                for i, step in enumerate(plan.steps, 1):
                    lines.append(f"{i}. **{step.tool}** ({step.description})")
                    lines.append(f"   Args: {step.args}")
                console.print(Markdown("\n".join(lines)))
            except Exception as e:
                console.print(f"[red]Plan error: {e}[/red]")
            continue

        # Regular message
        try:
            response = orchestrator.handle_message(user_input)
            console.print(Panel(Markdown(response), title="[bold blue]Agent[/bold blue]", expand=False))
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
