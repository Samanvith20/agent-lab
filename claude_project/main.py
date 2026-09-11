"""Command-line interface for indexing and querying a selected project."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from claude_project.agent.factory import build_agent
from claude_project.agent.orchestrator import handle_query
from claude_project.config.config import config
from claude_project.context.indexers.factory import get_indexer, get_index_inspector
from claude_project.llm.factory import get_embedder, get_llm
from claude_project.memory.session import get_current_session, new_session, switch_session

console = Console()


def initialize(repo_path: str):
    """Initialize the agent, index, and selected conversation session."""
    if not Path(repo_path).is_dir():
        raise ValueError(f"Project directory does not exist: {repo_path}")
    llm, embedder = get_llm(), get_embedder()
    console.print(f"Model: {config['llm']['model']} | Project: {repo_path}", markup=False)
    with console.status("Parsing and indexing project..."):
        index = get_indexer()(repo_path, embedder)
    try:
        return build_agent(llm, index), index, get_current_session()
    except Exception:
        index.client.close()
        raise


def report_error(exc: Exception) -> None:
    if isinstance(exc, ValueError):
        console.print(str(exc), style="red", markup=False)
    else:
        console.print(
            f"{type(exc).__name__}: request failed. Check API credentials, quota, and Qdrant connectivity.",
            style="red",
        )


def run() -> None:
    parser = argparse.ArgumentParser(description="Index and query a code project using OpenAI and Qdrant.")
    parser.add_argument("--project", default=str(Path.cwd()), help="Directory to index (default: current directory)")
    args = parser.parse_args()
    index = None
    try:
        agent, index, session_id = initialize(str(Path(args.project).resolve()))
        console.print("[green]Ready[/green] | /ask <question> | /new_session | /switch <id> | /session | /show_index | /exit")
        while True:
            try:
                command = Prompt.ask(">").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if command.lower() in ("/exit", "/quit"):
                break
            if not command:
                continue
            try:
                if command.startswith("/ask "):
                    with console.status("Searching and answering..."):
                        answer = handle_query(command[5:].strip(), agent, session_id)
                    console.print(answer, markup=False)
                elif command == "/new_session":
                    session_id = new_session()
                    console.print(f"New session started: {session_id}", style="green")
                elif command.startswith("/switch "):
                    session_id = switch_session(command.removeprefix("/switch "))
                    console.print(f"Switched to session: {session_id}", style="green")
                elif command == "/session":
                    console.print(f"Current session: {session_id}")
                elif command in {"/show_index", "/show_semantic_index"}:
                    get_index_inspector()(index)
                else:
                    console.print("Use /ask <question>, /new_session, /switch <id>, /session, /show_index, or /exit.")
            except KeyboardInterrupt:
                console.print("Request interrupted.")
            except Exception as exc:
                report_error(exc)
    except KeyboardInterrupt:
        console.print("Startup interrupted.")
    except Exception as exc:
        report_error(exc)
        raise SystemExit(1)
    finally:
        if index is not None:
            index.client.close()


if __name__ == "__main__":
    run()
