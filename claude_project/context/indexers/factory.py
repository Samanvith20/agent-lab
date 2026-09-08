from claude_project.config.config import config


def get_indexer():
    if config["vector_store"]["provider"] != "qdrant":
        raise ValueError("Only the Qdrant indexer is implemented.")
    from .semantic_qdrant import index_codebase
    return index_codebase


def get_index_inspector():
    get_indexer()
    from .semantic_qdrant import show_index
    return show_index
