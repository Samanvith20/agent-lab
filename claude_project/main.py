"""Interactive command-line entry point."""

from pathlib import Path
import sys

# Support direct script execution as well as the installed command.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from claude_project.observability.logger import get_logger

console = Console()
logger = get_logger(__name__)


def run() -> None:
    logger.info("Starting Educosys Claude")
    console.print("\n[bold blue]Educosys Claude[/bold blue] - RAG-powered code assistant")
    console.print("Type [bold]'/ask <question>'[/bold] or [bold]'/exit'[/bold] to quit\n")
    while True:
        try:
            user_input = Prompt.ask("[bold green]>[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not user_input:
            continue
        if user_input.lower() in ("/exit", "/quit"):
            break
        if user_input == "/ask" or user_input.startswith("/ask "):
            question = user_input.removeprefix("/ask").strip()
            if not question:
                console.print("[yellow]Usage: /ask <question>[/yellow]")
                continue
            logger.info("Ask command received: %s", question)
            console.print("Search and answer generation are not implemented yet.", style="dim")
        else:
            logger.warning("Unknown command received: %s", user_input)
            console.print("[yellow]Unknown command. Try:[/yellow]")
            console.print(" [bold]/ask <question>[/bold] - ask a question (not implemented yet)")
            console.print(" [bold]/exit[/bold] - quit")
    logger.info("Shutting down")
    console.print("[dim]Goodbye![/dim]")


if __name__ == "__main__":
    run()
