from functools import partial
from claude_project.config.config import config


def get_retriever(vector_store):
    if config["vector_store"]["provider"] != "qdrant":
        raise ValueError("Only the Qdrant retriever is implemented.")
    from .semantic_qdrant import retrieve
    return partial(retrieve, vector_store=vector_store)
