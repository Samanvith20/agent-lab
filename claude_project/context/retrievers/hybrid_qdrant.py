"""Retrieve top-k relevant code chunks using Qdrant Hybrid (Dense + Sparse BM25) Search."""
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def retrieve(query: str, vector_store, k: int = 5) -> list[dict]:
    """
    Search the hybrid repository vector store (dense + sparse vectors).
    Returns top-k code snippets with payload metadata and hybrid similarity scores.
    """
    logger.info(f"Retrieving top {k} chunks using Hybrid Search — query: {query}")
    results = vector_store.similarity_search_with_score(query, k=k)
    
    chunks = []
    for doc, score in results:
        meta = doc.metadata or {}
        chunks.append({
            "content": doc.page_content,
            "source": meta.get("source", "unknown"),
            "name": meta.get("name", "unknown"),
            "type": meta.get("type", "block"),
            "start_line": meta.get("start_line", 1),
            "end_line": meta.get("end_line", 1),
            "score": score,
        })
        logger.debug(f"Retrieved {meta.get('type')} '{meta.get('name')}' from {meta.get('source')} (score: {score:.4f})")
        
    return chunks