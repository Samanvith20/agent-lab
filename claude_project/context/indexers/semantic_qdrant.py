"""Index immutable repository snapshots in Qdrant."""
import hashlib
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from claude_project.config.config import config
from .code_parser import get_source_files, parse_file, _sliding_window


def index_codebase(repo_path: str, embedder, client=None):
    root = Path(repo_path).resolve()
    source_files = get_source_files(str(root))
    if not source_files:
        raise ValueError('No supported, non-empty source files found in this project.')

    # 1. Fast Pass: Calculate SHA-256 Digest using raw file bytes & relative paths ONLY
    digest = hashlib.sha256((str(root) + repr(config['embeddings']) + 'parser-v2').encode())
    for filepath in source_files:
        digest.update(str(Path(filepath).relative_to(root)).encode())
        digest.update(Path(filepath).read_bytes())

    name = config['qdrant']['collection_name'] + '_' + digest.hexdigest()[:24]
    url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    api_key = os.getenv('QDRANT_API_KEY') or None
    
    owned = client is None
    client = client or QdrantClient(url=url, api_key=api_key, timeout=30)
    
    try:
        # 2. FAST CHECK FIRST: If collection exists in Qdrant, return INSTANTLY (skip Tree-sitter parsing!)
        if client.collection_exists(name):
            count = client.count(name, exact=True).count
            if count > 0:
                return QdrantVectorStore(client=client, collection_name=name, embedding=embedder, validate_collection_config=False)

        # 3. Slow Pass: Only if collection is missing/changed, run Tree-sitter parse_file()!
        docs = []
        for filepath in source_files:
            for chunk in parse_file(filepath):
                parts = _sliding_window(chunk.content.splitlines(), filepath)
                for part in parts:
                    for offset in range(0, len(part.content), 6000):
                        docs.append(Document(page_content=part.content[offset:offset + 6000], metadata={
                            'source': str(Path(filepath).relative_to(root)),
                            'name': chunk.name,
                            'type': chunk.type,
                            'start_line': chunk.start_line + part.start_line - 1,
                            'end_line': chunk.start_line + part.end_line - 1,
                        }))

        vectors = embedder.embed_documents([docs[0].page_content])
        client.create_collection(name, vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE))
            
        store = QdrantVectorStore(client=client, collection_name=name, embedding=embedder, validate_collection_config=False)
        for start in range(0, len(docs), 50):
            batch = docs[start:start + 50]
            ids = [str(uuid5(NAMESPACE_URL, name + ':' + str(i))) for i in range(start, start + len(batch))]
            store.add_documents(batch, ids=ids)
            
        return store
    except Exception:
        if owned:
            client.close()
        raise


def show_index(vector_store):
    """Print metadata and previews using LangChain's nested payload format."""
    from rich.console import Console
    console = Console()
    offset = None
    while True:
        points, offset = vector_store.client.scroll(
            collection_name=vector_store.collection_name, offset=offset,
            with_payload=True, with_vectors=False, limit=100)
        for point in points:
            payload = point.payload or {}
            meta = payload.get('metadata', {})
            console.print(f"{meta.get('source')}:{meta.get('start_line')}-{meta.get('end_line')} | {meta.get('name')}", markup=False)
            console.print(payload.get('page_content', '')[:300], markup=False)
        if offset is None:
            break
