def handle_query(question: str, agent, thread_id: str) -> str:
    """Run one agent turn within the selected persistent conversation."""
    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}, "recursion_limit": 12},
    )
    return response["messages"][-1].content
