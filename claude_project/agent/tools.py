from langchain.tools import tool
from claude_project.context.retrievers.factory import get_retriever


def build_search_tool(vector_store):
    retrieve = get_retriever(vector_store)

    @tool
    def search_codebase(query: str) -> str:
        """Search the selected repository for relevant code and source locations."""
        chunks = retrieve(query, k=5)
        if not chunks:
            return "No relevant code found."
        return "\n---\n".join(
            f"File: {c['source']} (lines {c['start_line']}-{c['end_line']})\n"
            f"Type: {c['type']} - {c['name']}\nCode:\n{c['content']}"
            for c in chunks
        )
    return search_codebase
