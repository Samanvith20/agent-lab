# Agent Lab

Python 3.12+ codebase assistant using LangChain, OpenAI embeddings, and Qdrant.

## Run

From D:\agent-lab:

```powershell
poetry install
poetry run agent --project "D:\path\to\your\project"
```

Without `--project`, the current directory is indexed. Startup sends eligible
source chunks to the configured embedding provider and stores code and metadata
in Qdrant. Start with a small project you intend to send to those services.

Set these in the existing project `.env` (never commit actual keys):

```dotenv
OPENAI_API_KEY=your-key
QDRANT_URL=http://localhost:6333
# Required for Qdrant Cloud or an authenticated server:
QDRANT_API_KEY=your-qdrant-key
```

Use your cluster URL for Qdrant Cloud. A local Qdrant server must already be running
on port 6333 with persistent storage. OpenAI API billing/quota must support both
the chat and embedding models in `claude_project/config/config.yaml`.

## Flow

1. Load `.env`; create one chat client and one embedder.
2. Scan the selected project, excluding common build/dependency directories,
   symlinks, `.env*`, files over 1 MB, and files matched by Git ignore rules when Git is available.
3. Parse supported code languages with Tree-sitter. Preserve functions/classes
   and top-level statements; split text/config files and large blocks into chunks.
4. Hash project path, eligible file contents, parser version, and embedding
   settings to choose a repository snapshot collection in Qdrant.
5. Reuse a complete unchanged snapshot; otherwise embed/upsert chunks using stable IDs.
6. Build one LangChain agent with a search tool bound to that exact vector store.
7. `/ask` lets the agent query the tool, which embeds the question and retrieves
   five similar chunks. The model answers with file and line references.

Commands: `/ask <question>`, `/show_semantic_index`, `/exit`, `/quit`.
The agent has a 12-step recursion limit. Questions are independent; conversation
history is not persisted. A prompt asks the agent to search; this is not a hard
programmatic guarantee that every answer calls the tool.

## Tests

```powershell
poetry run python -m unittest discover -s tests -v
poetry run agent --help
```

Tests use in-memory Qdrant and fake embeddings/chat responses: no API spend.
They cover imports, Unicode parsing, exclusions, retrieval, tool execution,
unchanged-index reuse, changed content, repository separation and inspection.

## Current limits before broader deployment

- Restart after changing source files or configuration to select a new snapshot.
- Snapshots retain old collections. Storage cleanup and retention are not automated.
- Indexing is intended for one writer per project, not concurrent distributed ingestion.
- Ignore rules are not secret detection; review eligible files before indexing.
- Language grammar failures fall back to line chunks. Parsing is not compilation.
- Hugging Face embeddings additionally require `sentence-transformers`; the current
  configuration uses OpenAI, so this extra package is not needed.
- Retrieval is semantic only. Elasticsearch/hybrid search, reranking, access control,
  tenant authentication, backups and retrieval-quality evaluation are not implemented.
- Existing legacy `codebase` collections are not deleted or reused by the snapshot scheme.

The CLI entry point remains `poetry run agent`, mapped to `claude_project.main:run`.

## Global command installed with pipx

The global `agent` command uses its own pipx environment, separate from Poetry.
After adding dependencies to `pyproject.toml`, update that environment:

```powershell
python -m pipx runpip agent-lab install --editable D:\agent-lab
```

Then run `agent --help` to verify imports, or run `agent` from the project you
want to index. An editable install picks up source edits automatically, but new
dependencies require the update command above.
