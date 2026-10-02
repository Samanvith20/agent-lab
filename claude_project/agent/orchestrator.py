from langchain_core.messages import AIMessage, RemoveMessage, ToolMessage

from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def _drop_trailing_incomplete_tool_calls(messages: list) -> list:
    """Remove only dangling assistant tool calls left by an interrupted turn."""
    if not messages:
        return messages

    pending = {
        call["id"]
        for call in getattr(messages[-1], "tool_calls", [])
        if call.get("id")
    } if isinstance(messages[-1], AIMessage) else set()
    if not pending:
        return messages

    # Tool messages may follow the assistant message in a completed tool round.
    # Only repair when the checkpoint actually ends with unresolved calls.
    for message in messages:
        if isinstance(message, ToolMessage):
            pending.discard(message.tool_call_id)
    if not pending:
        return messages

    logger.warning(
        "Removing a trailing assistant message with %d unresolved tool call(s) "
        "from the restored conversation checkpoint",
        len(pending),
    )
    return messages[:-1]

async def handle_query(question: str, agent, thread_id: str) -> str:
    """Run one async agent turn so MCP tools can execute asynchronously."""
    thread_config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(thread_config)
    messages = _drop_trailing_incomplete_tool_calls(
        list((state.values or {}).get("messages", []))
    )
    checkpoint_messages = list((state.values or {}).get("messages", []))
    if len(messages) != len(checkpoint_messages):
        # Restore a valid checkpoint before invoking the model again. The reducer
        # removes only the dangling assistant tool-call message.
        await agent.aupdate_state(
            thread_config,
            {"messages": [RemoveMessage(id=checkpoint_messages[-1].id)]},
        )
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config={**thread_config, "recursion_limit": 12},
    )
    return response["messages"][-1].content
