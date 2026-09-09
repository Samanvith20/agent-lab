"""Index immutable repository snapshots in Qdrant with Hybrid (Dense + Sparse BM25) Search."""
import hashlib
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from qdrant_client import QdrantClient

from claude_project.config.config import config
from claude_project.observability.logger import get_logger
from .code_parser import get_source_files, parse_file, _sliding_window

logger = get_logger(__name__)

RETRIEVAL_MODE_MAP = {
    "dense": RetrievalMode.DENSE,
    "sparse": RetrievalMode.SPARSE,
    "hybrid": RetrievalMode.HYBRID,
}


def _get_retrieval_mode() -> RetrievalMode:
    mode = config["vector_store"].get("retrieval_mode", "hybrid")
    return RETRIEVAL_MODE_MAP.get(mode, RetrievalMode.HYBRID)


def index_codebase(repo_path: str, embedder, client=None) -> QdrantVectorStore:
    """
    Parse all source files, embed with dense + sparse vectors, and store in Qdrant.
    Optimized to check Qdrant snapshot collection FIRST before running Tree-sitter parsing.
    """
    root = Path(repo_path).resolve()
    source_files = get_source_files(str(root))
    if not source_files:
        raise ValueError("No supported, non-empty source files found in this project.")

    # 1. Fast Pass: Calculate SHA-256 Digest using raw file bytes & relative paths ONLY
    digest = hashlib.sha256((str(root) + repr(config["embeddings"]) + "parser-hybrid-v1").encode())
    for filepath in source_files:
        digest.update(str(Path(filepath).relative_to(root)).encode())
        digest.update(Path(filepath).read_bytes())

    collection_name = config["qdrant"]["collection_name"] + "_hybrid_" + digest.hexdigest()[:20]
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY") or None
    retrieval_mode = _get_retrieval_mode()
    
    owned = client is None
    client = client or QdrantClient(url=url, api_key=api_key, timeout=30)
    
    try:
        sparse_embedder = FastEmbedSparse(model_name="Qdrant/bm25")
        
        # 2. FAST CHECK FIRST: If collection exists in Qdrant, return INSTANTLY (skip Tree-sitter parsing!)
        if client.collection_exists(collection_name):
            count = client.count(collection_name, exact=True).count
            if count > 0:
                logger.info(f"Loaded existing unchanged hybrid collection {collection_name} with {count} chunks (skipped parsing)")
                return QdrantVectorStore.from_existing_collection(
                    embedding=embedder,
                    sparse_embedding=sparse_embedder,
                    retrieval_mode=retrieval_mode,
                    url=url,
                    api_key=api_key,
                    collection_name=collection_name,
                )

        # 3. Slow Pass: Only if collection is missing/changed, run Tree-sitter parse_file()!
        logger.info(f"Starting hybrid indexing of {repo_path} into collection {collection_name}")
        docs = []
        for filepath in source_files:
            for chunk in parse_file(filepath):
                parts = _sliding_window(chunk.content.splitlines(), filepath)
                for part in parts:
                    for offset in range(0, len(part.content), 6000):
                        docs.append(Document(
                            page_content=part.content[offset:offset + 6000],
                            metadata={
                                "source": str(Path(filepath).relative_to(root)),
                                "name": chunk.name,
                                "type": chunk.type,
                                "start_line": chunk.start_line + part.start_line - 1,
                                "end_line": chunk.start_line + part.end_line - 1,
                            }
                        ))

        ids = [str(uuid5(NAMESPACE_URL, collection_name + ":" + str(i))) for i in range(len(docs))]
        store = QdrantVectorStore.from_documents(
            docs,
            embedding=embedder,
            sparse_embedding=sparse_embedder,
            retrieval_mode=retrieval_mode,
            url=url,
            api_key=api_key,
            collection_name=collection_name,
            ids=ids,
            batch_size=50,
        )
        logger.info(f"Hybrid indexing complete. Total chunks indexed: {len(docs)}")
        return store
    except Exception:
        if owned:
            client.close()
        raise


def show_index(vector_store: QdrantVectorStore) -> None:
    """Print hybrid index metadata and payload previews."""
    from rich.console import Console
    console = Console()
    offset = None
    while True:
        points, offset = vector_store.client.scroll(
            collection_name=vector_store.collection_name,
            offset=offset,
            with_payload=True,
            with_vectors=False,
            limit=100,
        )
        for point in points:
            payload = point.payload or {}
            meta = payload.get("metadata", {})
            console.print(
                f"{meta.get('source')}:{meta.get('start_line')}-{meta.get('end_line')} | {meta.get('name')} ({meta.get('type')})",
                markup=False
            )
            console.print(payload.get("page_content", "")[:300], markup=False)
        if offset is None:
            break