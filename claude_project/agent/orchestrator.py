def handle_query(question: str, agent) -> str:
    """Run a bounded agent turn using the initialized model and repository tool."""
    response = agent.invoke({"messages": [{"role": "user", "content": question}]},
                            config={"recursion_limit": 12})
    return response["messages"][-1].text
