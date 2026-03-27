"""CLI entry point — Rich-based REPL."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Import tool modules to trigger @tool registration
import felix.tools.finance  # noqa: F401
import felix.tools.search  # noqa: F401
from felix.agent import Agent
from felix.llm import DEFAULT_MODEL


def main() -> None:
    load_dotenv()
    console = Console()
    model = os.environ.get("FELIX_MODEL", DEFAULT_MODEL)

    console.print(
        Panel(
            f"[bold]Felix[/bold] — Financial Research Agent\n"
            f"Model: {model}\n"
            f"Type [bold]/quit[/bold] to exit, [bold]/model[/bold] to switch model",
            border_style="blue",
        )
    )

    agent = Agent(model=model)

    while True:
        try:
            query = console.input("\n[bold blue]>[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not query:
            continue
        if query in ("/quit", "/exit", "/q"):
            break
        if query.startswith("/model"):
            parts = query.split(maxsplit=1)
            if len(parts) > 1:
                model = parts[1]
            else:
                model = console.input("Model: ").strip()
            agent = Agent(model=model)
            console.print(f"Switched to [bold]{model}[/bold]")
            continue

        try:
            for event in agent.run(query):
                _render_event(console, event)
        except KeyboardInterrupt:
            console.print("\n[dim](interrupted)[/dim]")
            continue

    console.print("\n[dim]Bye![/dim]")


def _render_event(console: Console, event: dict) -> None:
    match event["type"]:
        case "thinking":
            console.print(f"[dim italic]{event['message']}[/dim italic]")
        case "tool_start":
            args_str = ", ".join(
                f"{k}={v}" for k, v in event.get("args", {}).items()
            )
            console.print(f"  [yellow]\u2192 {event['tool']}({args_str})[/yellow]")
        case "tool_end":
            result = event.get("result", "")
            if len(result) > 200:
                result = result[:200] + "\u2026"
            console.print(f"  [dim]{result}[/dim]")
        case "error":
            console.print(f"[red]Error: {event['message']}[/red]")
        case "done":
            answer = event.get("answer", "")
            if answer:
                console.print()
                console.print(Markdown(answer))
            iters = event.get("iterations", 0)
            console.print(
                f"\n[dim]({iters} iteration{'s' if iters != 1 else ''})[/dim]"
            )


if __name__ == "__main__":
    main()
