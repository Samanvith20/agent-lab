"""Command-line interface for indexing and querying a selected project."""
import argparse
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

from claude_project.config.config import config
from claude_project.context.indexers.factory import get_indexer, get_index_inspector
from claude_project.llm.factory import get_llm, get_embedder
from claude_project.agent.factory import build_agent
from claude_project.agent.orchestrator import handle_query

console = Console()


def initialize(repo_path):
    if not Path(repo_path).is_dir():
        raise ValueError(f'Project directory does not exist: {repo_path}')
    llm, embedder = get_llm(), get_embedder()
    console.print(f"Model: {config['llm']['model']} | Project: {repo_path}", markup=False)
    with console.status('Parsing and indexing project...'):
        index = get_indexer()(repo_path, embedder)
    try:
        return build_agent(llm, index), index
    except Exception:
        index.client.close()
        raise


def report_error(exc):
    # Provider exception bodies may contain request data; show only actionable categories.
    if isinstance(exc, ValueError):
        console.print(str(exc), style='red', markup=False)
    else:
        console.print(f'{type(exc).__name__}: request failed. Check API credentials, quota, and Qdrant connectivity.', style='red')


def run():
    parser = argparse.ArgumentParser(description='Index and query a code project using OpenAI and Qdrant.')
    parser.add_argument('--project', default=str(Path.cwd()), help='Directory to index (default: current directory)')
    args = parser.parse_args()
    index = None
    try:
        agent, index = initialize(str(Path(args.project).resolve()))
        console.print('[green]Ready[/green] | /ask <question> | /show_semantic_index | /exit')
        while True:
            try:
                command = Prompt.ask('>').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if command.lower() in ('/exit', '/quit'):
                break
            if not command:
                continue
            try:
                if command.startswith('/ask '):
                    with console.status('Searching and answering...'):
                        answer = handle_query(command[5:].strip(), agent)
                    console.print(answer, markup=False)
                elif command == '/show_semantic_index':
                    get_index_inspector()(index)
                else:
                    console.print('Use /ask <question>, /show_semantic_index, or /exit.')
            except KeyboardInterrupt:
                console.print('Request interrupted.')
            except Exception as exc:
                report_error(exc)
    except KeyboardInterrupt:
        console.print('Startup interrupted.')
    except Exception as exc:
        report_error(exc)
        raise SystemExit(1)
    finally:
        if index is not None:
            index.client.close()
