"""SQLite-backed conversation memory and context summarization."""

import sqlite3
from pathlib import Path

from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.sqlite import SqliteSaver

from claude_project.config.config import config
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def memory_db_path() -> Path:
    """Return the configured database path and create its parent directory."""
    db_path = Path(config["memory"]["db_path"]).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_checkpointer() -> SqliteSaver:
    """Create a SQLite checkpointer for the lifetime of an agent."""
    db_path = memory_db_path()
    logger.info("Using SQLite checkpointer at %s", db_path)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(connection)


def get_session_history(thread_id: str) -> list[dict[str, str]]:
    """Return the latest persisted messages for a thread, if it exists."""
    checkpointer = get_checkpointer()
    checkpoint = checkpointer.get({"configurable": {"thread_id": thread_id}})
    if not checkpoint:
        return []

    messages = checkpoint["channel_values"].get("messages", [])
    return [
        {"role": _message_role(message.type), "content": str(message.content)}
        for message in messages
    ]


def get_summarization_middleware(model) -> SummarizationMiddleware:
    """Keep recent messages and summarize older context before it grows too large."""
    memory_config = config["memory"]
    return SummarizationMiddleware(
        model=model,
        trigger=("tokens", memory_config["summarize_at_tokens"]),
        keep=("messages", memory_config["keep_last_messages"]),
    )


def _message_role(message_type: str) -> str:
    return {"human": "user", "ai": "assistant", "tool": "tool"}.get(message_type, "system")
