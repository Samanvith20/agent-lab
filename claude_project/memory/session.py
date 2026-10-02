"""Persist the currently selected conversation session."""

import uuid
from pathlib import Path

from claude_project.memory.short_term import memory_db_path
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def _session_file() -> Path:
    return memory_db_path().parent / "current_session"


def get_current_session() -> str:
    """Return the saved session ID, creating one when absent or empty."""
    session_file = _session_file()
    if session_file.exists():
        session_id = session_file.read_text(encoding="utf-8").strip()
        if session_id:
            logger.info("Resuming session: %s", session_id)
            return session_id
    return new_session()


def new_session() -> str:
    """Create and select a fresh conversation session."""
    session_id = str(uuid.uuid4())
    _write_session(session_id)
    logger.info("Started new session: %s", session_id)
    return session_id


def switch_session(session_id: str) -> str:
    """Select a LangGraph thread ID for subsequent messages."""
    session_id = session_id.strip()
    if not session_id:
        raise ValueError("A session ID is required.")
    _write_session(session_id)
    logger.info("Switched to session: %s", session_id)
    return session_id


def _write_session(session_id: str) -> None:
    _session_file().write_text(session_id, encoding="utf-8")