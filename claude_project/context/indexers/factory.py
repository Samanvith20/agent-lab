from claude_project.config.config import config
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def get_indexer():
    provider = config.get("vector_store", {}).get("provider", "qdrant")
    mode = config.get("rag", {}).get("mode", "semantic")
    
    if provider != "qdrant":
        raise ValueError("Only Qdrant vector store is supported.")
    
    if mode == "hybrid":
        from .hybrid_qdrant import index_codebase
    else:
        from .semantic_qdrant import index_codebase
        
    return index_codebase


def get_index_inspector():
    """Return the show_index function based on rag mode in config."""
    provider = config.get("vector_store", {}).get("provider", "qdrant")
    mode = config.get("rag", {}).get("mode", "semantic")
    
    if provider != "qdrant":
        raise ValueError("Only Qdrant vector store is supported.")
        
    if mode == "hybrid":
        from .hybrid_qdrant import show_index
    else:
        from .semantic_qdrant import show_index
        
    return show_index