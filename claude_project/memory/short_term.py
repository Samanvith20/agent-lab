"""Async SQLite-backed conversation memory and context summarization."""

from pathlib import Path
from contextlib import AbstractAsyncContextManager

from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from claude_project.config.config import config
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def memory_db_path() -> Path:
    """Return the configured database path and create its parent directory."""
    db_path = Path(config["memory"]["db_path"]).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_checkpointer() -> AbstractAsyncContextManager[AsyncSqliteSaver]:
    """Return an async SQLite saver context that owns its database connection."""
    db_path = memory_db_path()
    logger.info("Using SQLite checkpointer at %s", db_path)
    return AsyncSqliteSaver.from_conn_string(str(db_path))


async def get_session_history(
    thread_id: str, checkpointer: AsyncSqliteSaver
) -> list[dict[str, str]]:
    """Return the latest persisted messages for a thread, if it exists."""
    checkpoint = await checkpointer.aget({"configurable": {"thread_id": thread_id}})
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
