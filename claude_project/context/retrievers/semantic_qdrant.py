def retrieve(query: str, vector_store, k: int = 5) -> list[dict]:
    """Search the same repository snapshot that was indexed at startup."""
    return [dict(doc.metadata, content=doc.page_content, score=score)
            for doc, score in vector_store.similarity_search_with_score(query, k=k)]
