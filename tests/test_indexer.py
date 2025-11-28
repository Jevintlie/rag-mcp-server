import json, glob
from pathlib import Path
from src.rag_mcp.index.chunker import make_chunks
from src.rag_mcp.config import JSON_DIR

def test_chunk_counts():
    for fp in glob.glob(str(Path(JSON_DIR) / "*.json")):
        p = json.loads(Path(fp).read_text(encoding="utf-8"))
        chunks = make_chunks(p)
        assert any(c["metadata"]["section"]=="fees" for c in chunks)
