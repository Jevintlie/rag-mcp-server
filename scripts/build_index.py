import argparse, json, glob
from pathlib import Path
from src.rag_mcp.config import JSON_DIR, CHROMA_DIR, COLLECTION
from src.rag_mcp.index.chunker import make_chunks
from src.rag_mcp.index.store_chroma import get_collection, upsert_chunks

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="programme id slug (matches filename)", default=None)
    args = ap.parse_args()

    files = glob.glob(str(Path(JSON_DIR) / "*.json"))
    if args.only:
        files = [f for f in files if Path(f).stem.endswith(args.only.split(":")[-1])]
    client, col = get_collection(CHROMA_DIR, COLLECTION)
    total = 0
    for fp in files:
        p = json.loads(Path(fp).read_text(encoding="utf-8"))
        chunks = make_chunks(p)
        upsert_chunks(client, col, chunks)
        total += len(chunks)
    print(f"Upserted {total} chunks to collection {COLLECTION} at {CHROMA_DIR}")
