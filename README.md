# University Programme RAG MCP Server

This capstone project provides structured, source-linked university programme information through a retrieval-augmented Model Context Protocol (MCP) server. It ingests saved programme pages, normalizes them into a validated schema, creates retrieval-focused chunks, stores embeddings in ChromaDB, and exposes search and document lookup tools over JSON-RPC stdio.

The server was designed and implemented by Jevint Felixciano as the retrieval component of an embodied university-enquiry assistant. The avatar interface used the third-party Open-LLM-VTuber project as an integration client; that upstream project is not included or presented as original work here.

## Architecture

```text
saved source pages
       |
HTML extraction and normalization
       |
JSON Schema validation
       |
retrieval-focused chunking
       |
ChromaDB + sentence embeddings + optional reranking
       |
MCP tools: rag.search and rag.get
       |
avatar or other MCP client
```

## What is included

- A Python package and `sunway-rag-mcp` command
- Programme, request, and response JSON Schemas
- Deterministic ingestion and chunking scripts
- MCP initialization, tool discovery, search, and lookup handlers
- Offline fixtures and tests that do not download model weights
- Docker configuration for a source-only runtime

## What is intentionally excluded

- Downloaded embedding and reranking model files
- Chroma vector databases
- Raw copies of university webpages
- Local virtual environments, bytecode, and private client configuration

Those artifacts made the original public repository unnecessarily large and difficult to reproduce. Models are now resolved by name through `sentence-transformers`, and data paths are configurable.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
python -m pip install -e ".[dev]"
copy .env.example .env
```

Set `DATA_DIR` to a local directory containing `json/` and `chroma/`. The sample under `tests/fixtures` is synthetic and is only intended for tests.

## Build an index

After placing licensed or locally captured programme HTML in `data/html/`:

```bash
python scripts/sync_batch.py --glob "data/html/*.html"
python scripts/build_index.py
```

Review the source website's terms and robots policy before collecting content. Programme facts, fees, and intake dates change over time, so a production deployment must display source URLs and freshness metadata.

## Run the MCP server

```bash
sunway-rag-mcp --stdio
```

An example client entry is available in [`mcp_servers.example.json`](mcp_servers.example.json).

## Test

```bash
pytest
```

The offline suite checks schema enforcement, stable chunk IDs, query intent routing, Chroma filters, request validation, and the MCP capability/tool contract.

## Known limitations

- The current stdio transport implements the required JSON-RPC/MCP subset directly rather than depending on an MCP SDK.
- Programme-name matching and cross-encoder reranking load local models on first use.
- Long-term operation requires scheduled source refreshes and regression evaluation against a versioned question set.
