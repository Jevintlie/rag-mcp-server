from typing import Optional

from sentence_transformers import SentenceTransformer

from ..config import EMBED_MODEL  # make sure this points to ./models/all-MiniLM-L6-v2

_embedder: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    """
    Lazily load and cache the SentenceTransformer embedder.

    Strictly offline: local_files_only=True means it will only load
    from EMBED_MODEL (local folder or local HF cache) and never
    attempt to download from the internet.
    """
    global _embedder

    if _embedder is not None:
        return _embedder

    try:
        _embedder = SentenceTransformer(EMBED_MODEL, local_files_only=True)
    except Exception as e:
        raise RuntimeError(
            f"[RAG] Failed to load embedder model from '{EMBED_MODEL}'. "
            f"Make sure the folder exists and contains a valid SentenceTransformer model."
        ) from e

    return _embedder


def encode(texts, convert_to_numpy: bool = True):
    """
    Convenience wrapper around SentenceTransformer.encode with
    normalization turned on.
    """
    model = get_embedder()
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=convert_to_numpy,
    )
