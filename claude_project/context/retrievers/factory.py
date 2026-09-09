from functools import partial
from claude_project.config.config import config
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def get_retriever(vector_store):
    provider = config.get("vector_store", {}).get("provider", "qdrant")
    mode = config.get("rag", {}).get("mode", "semantic")
    
    if provider != "qdrant":
        raise ValueError("Only Qdrant vector store is supported.")
        
    if mode == "hybrid":
        from .hybrid_qdrant import retrieve
    else:
        from .semantic_qdrant import retrieve
        
    return partial(retrieve, vector_store=vector_store)