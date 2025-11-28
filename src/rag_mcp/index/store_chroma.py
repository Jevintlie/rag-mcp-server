import chromadb
from chromadb.config import Settings
from typing import List, Dict

def get_collection(persist_dir: str, name: str):
    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=False))
    col = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    return client, col

def upsert_chunks(client, collection, chunks: List[Dict]):
    ids = [c["id"] for c in chunks]
    docs = [c["text"] for c in chunks]
    metas = [c["metadata"] for c in chunks]
    # embeddings computed client-side by embedder when bulk indexing; for demo, let Chroma compute later if needed
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    # Persist handled by PersistentClient; nothing else required
